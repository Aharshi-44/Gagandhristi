import os
import sys
import json

import torch
import numpy as np
from PIL import Image
import cv2


# ============================================================
# PROJECT ROOT
# ============================================================

PROCESSING_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROCESSING_ROOT not in sys.path:
    sys.path.insert(
        0,
        PROCESSING_ROOT
    )


# ============================================================
# PROJECT IMPORTS
# ============================================================

from models.siamese_unet import SiameseUNet

from preprocessing.preprocess import (
    load_and_preprocess
)

from inference.change_analysis import (
    analyze_mask
)

from inference.vegetation_analysis import (
    detect_vegetation_change,
    create_vegetation_overlay
)

from inference.pixel_diff_analysis import (
    detect_pixel_diff_change,
    create_pixel_diff_overlay
)

from inference.geotiff_handler import (
    is_geotiff,
    extract_geotiff_metadata,
    convert_geotiff_for_inference,
    convert_regions_to_gps
)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_THRESHOLD = 0.25

MODEL_PATH = os.path.join(
    PROCESSING_ROOT,
    "weights",
    "siamese_unet_levir_cd.pth"
)


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# CHANGE PROCESSOR
# ============================================================

class ChangeProcessor:

    def __init__(
        self,
        model_path=MODEL_PATH,
        threshold=DEFAULT_THRESHOLD
    ):
        self.model_path = model_path
        self.threshold = threshold
        self.device = DEVICE
        self.model = None

        self._load_model()


    # ========================================================
    # LOAD MODEL
    # ========================================================

    def _load_model(self):
        print("Loading Siamese U-Net...")

        self.model = SiameseUNet(
            in_channels=3
        )

        checkpoint = torch.load(
            self.model_path,
            map_location=self.device
        )

        self.model.load_state_dict(
            checkpoint,
            strict=True
        )

        self.model = self.model.to(
            self.device
        )

        self.model.eval()

        print("[OK] Siamese U-Net loaded")
        print("Device:", self.device)


    # ========================================================
    # RUN STRUCTURAL MODEL (SIAMESE U-NET)
    # ========================================================

    def _run_model(
        self,
        t1_path,
        t2_path
    ):
        image1 = load_and_preprocess(t1_path)
        image2 = load_and_preprocess(t2_path)

        if image1.shape != image2.shape:
            raise ValueError(
                "T1 and T2 must have identical dimensions. "
                f"T1={image1.shape}, T2={image2.shape}"
            )

        image1 = image1.to(self.device)
        image2 = image2.to(self.device)

        with torch.no_grad():
            logits = self.model(image1, image2)
            probability = torch.sigmoid(logits)

        probability_map = probability.squeeze().cpu().numpy()
        prediction_mask = (probability_map >= self.threshold).astype(np.uint8)

        return probability_map, prediction_mask


    # ========================================================
    # SAVE BINARY MASK
    # ========================================================

    def save_mask(
        self,
        mask,
        output_path
    ):
        output = (mask * 255).astype(np.uint8)
        Image.fromarray(output).save(output_path)


    # ========================================================
    # CREATE STRUCTURAL CHANGE OVERLAY
    # ========================================================

    def create_change_overlay(
        self,
        t2_path,
        mask,
        output_path,
        alpha=0.45
    ):
        """
        Creates an overlay of the predicted change mask on top of the T2 image.
        Changed pixels are highlighted in red.
        """
        image = cv2.imread(t2_path, cv2.IMREAD_COLOR)

        if image is None:
            raise FileNotFoundError(f"Could not load T2 image: {t2_path}")

        if mask.shape[0] != image.shape[0] or mask.shape[1] != image.shape[1]:
            mask = cv2.resize(
                mask,
                (image.shape[1], image.shape[0]),
                interpolation=cv2.INTER_NEAREST
            )

        overlay = np.zeros_like(image)
        overlay[:, :, 2] = 255  # Red in BGR

        change_pixels = (mask > 0)
        result = image.copy()

        if np.any(change_pixels):
            result[change_pixels] = cv2.addWeighted(
                image[change_pixels],
                1 - alpha,
                overlay[change_pixels],
                alpha,
                0
            )

        success = cv2.imwrite(output_path, result)
        if not success:
            raise IOError(f"Failed to save overlay: {output_path}")

        return output_path


    # ========================================================
    # PROCESS IMAGE PAIR WITH SPECIFIED CHANNEL
    # ========================================================

    def process(
        self,
        t1_path,
        t2_path,
        output_mask_path=None,
        channel_type="structural"
    ):
        """
        Complete multi-model change detection pipeline.

        Supported channel_type values:
        - "structural" / "STRUCTURAL_DL": Siamese U-Net building/infrastructure change
        - "vegetation" / "VEGETATION_NDVI": NDVI/VARI vegetation clearance & regrowth
        - "pixel_diff" / "PIXEL_DIFFERENCE": Radiometric Change Vector Analysis (CVA)
        """
        if not os.path.exists(t1_path):
            raise FileNotFoundError(f"T1 image not found: {t1_path}")

        if not os.path.exists(t2_path):
            raise FileNotFoundError(f"T2 image not found: {t2_path}")

        norm_channel = (channel_type or "structural").lower().strip()

        # Ensure output directory exists if output path given
        output_directory = None
        overlay_path = None

        if output_mask_path is not None:
            output_directory = os.path.dirname(output_mask_path)
            if output_directory:
                os.makedirs(output_directory, exist_ok=True)
            overlay_path = os.path.join(output_directory, "change_overlay.png")

        # ----------------------------------------------------
        # GEOTIFF DETECTION & PREPROCESSING (PS 2.2.6)
        # ----------------------------------------------------
        is_geo_t1 = is_geotiff(t1_path)
        is_geo_t2 = is_geotiff(t2_path)
        is_geo = is_geo_t1 or is_geo_t2

        geotiff_metadata = None
        t1_effective_path = t1_path
        t2_effective_path = t2_path
        t1_effective_rgb = None
        t2_effective_rgb = None
        t1_preview_path = None
        t2_preview_path = None
        t1_nir = None
        t2_nir = None

        if is_geo:
            print(f"\n[Processor] GeoTIFF input detected (T1: {is_geo_t1}, T2: {is_geo_t2})")
            t1_preview_path = os.path.join(output_directory, "T1_preview.png") if output_directory else None
            t2_preview_path = os.path.join(output_directory, "T2_preview.png") if output_directory else None

            if is_geo_t1:
                t1_effective_rgb, t1_nir, t1_meta = convert_geotiff_for_inference(t1_path, t1_preview_path)
                t1_effective_path = t1_preview_path if (t1_preview_path and os.path.exists(t1_preview_path)) else t1_path
            else:
                t1_bgr = cv2.imread(t1_path)
                t1_effective_rgb = cv2.cvtColor(t1_bgr, cv2.COLOR_BGR2RGB) if t1_bgr is not None else None
                t1_meta = {"is_geotiff": False}

            if is_geo_t2:
                t2_effective_rgb, t2_nir, t2_meta = convert_geotiff_for_inference(t2_path, t2_preview_path)
                t2_effective_path = t2_preview_path if (t2_preview_path and os.path.exists(t2_preview_path)) else t2_path
                geotiff_metadata = t2_meta
            else:
                t2_bgr = cv2.imread(t2_path)
                t2_effective_rgb = cv2.cvtColor(t2_bgr, cv2.COLOR_BGR2RGB) if t2_bgr is not None else None
                geotiff_metadata = t1_meta if t1_meta.get("is_geotiff") else None

        # ----------------------------------------------------
        # BRANCH 1: VEGETATION CHANGE (NDVI / VARI)
        # ----------------------------------------------------
        if norm_channel in {"vegetation", "vegetation_ndvi", "ndvi", "2"}:
            print(f"\n[Processor] Running Vegetation Analysis (NDVI/VARI)...")

            if t1_effective_rgb is not None and t2_effective_rgb is not None:
                if t1_nir is not None and t2_nir is not None:
                    # 4-band multi-spectral NIR stack for true NDVI
                    t1_input = np.dstack([t1_effective_rgb, t1_nir])
                    t2_input = np.dstack([t2_effective_rgb, t2_nir])
                else:
                    t1_input = t1_effective_rgb
                    t2_input = t2_effective_rgb
                t2_bgr = cv2.cvtColor(t2_effective_rgb, cv2.COLOR_RGB2BGR)
            else:
                # Load images as RGB
                t1_bgr = cv2.imread(t1_effective_path)
                t2_bgr = cv2.imread(t2_effective_path)

                if t1_bgr is None or t2_bgr is None:
                    raise ValueError("Could not read T1 or T2 image for vegetation analysis.")

                t1_input = cv2.cvtColor(t1_bgr, cv2.COLOR_BGR2RGB)
                t2_input = cv2.cvtColor(t2_bgr, cv2.COLOR_BGR2RGB)

            veg_result = detect_vegetation_change(t1_input, t2_input)
            cleaned_mask = veg_result["loss_mask"]

            if output_mask_path is not None:
                self.save_mask(cleaned_mask, output_mask_path)
                overlay_bgr = create_vegetation_overlay(
                    t2_bgr,
                    veg_result["loss_mask"],
                    veg_result["gain_mask"]
                )
                cv2.imwrite(overlay_path, overlay_bgr)

            analysis = {
                "change_detected": bool(veg_result["change_percentage"] > 0),
                "change_percentage": veg_result["change_percentage"],
                "severity": veg_result["severity"],
                "number_of_regions": veg_result["total_regions"],
                "regions": veg_result["regions"],
                "vegetation_loss_percentage": veg_result["loss_percentage"],
                "vegetation_gain_percentage": veg_result["gain_percentage"],
                "index_used": veg_result["index_used"]
            }

            result = {
                "channel_type": "VEGETATION_NDVI",
                "model": f"Vegetation Index ({veg_result['index_used']})",
                "threshold": 0.12,
                "device": "CPU (NumPy/OpenCV)",
                "change_detection": analysis
            }

        # ----------------------------------------------------
        # BRANCH 2: ALL PIXEL-TO-PIXEL CHANGE (CVA)
        # ----------------------------------------------------
        elif norm_channel in {"pixel_diff", "pixel_difference", "pixel", "diff", "3"}:
            print(f"\n[Processor] Running Pixel-to-Pixel Radiometric Diff (CVA)...")

            if t1_effective_rgb is not None and t2_effective_rgb is not None:
                t1_rgb = t1_effective_rgb
                t2_rgb = t2_effective_rgb
                t2_bgr = cv2.cvtColor(t2_effective_rgb, cv2.COLOR_RGB2BGR)
            else:
                t1_bgr = cv2.imread(t1_effective_path)
                t2_bgr = cv2.imread(t2_effective_path)

                if t1_bgr is None or t2_bgr is None:
                    raise ValueError("Could not read T1 or T2 image for pixel diff analysis.")

                t1_rgb = cv2.cvtColor(t1_bgr, cv2.COLOR_BGR2RGB)
                t2_rgb = cv2.cvtColor(t2_bgr, cv2.COLOR_BGR2RGB)

            diff_result = detect_pixel_diff_change(t1_rgb, t2_rgb)
            cleaned_mask = diff_result["mask"]

            if output_mask_path is not None:
                self.save_mask(cleaned_mask, output_mask_path)
                overlay_bgr = create_pixel_diff_overlay(t2_bgr, cleaned_mask)
                cv2.imwrite(overlay_path, overlay_bgr)

            analysis = {
                "change_detected": bool(diff_result["change_percentage"] > 0),
                "change_percentage": diff_result["change_percentage"],
                "severity": diff_result["severity"],
                "number_of_regions": diff_result["total_regions"],
                "regions": diff_result["regions"],
                "algorithm": diff_result["algorithm"]
            }

            result = {
                "channel_type": "PIXEL_DIFFERENCE",
                "model": "Radiometric Change Vector Analysis (CVA)",
                "threshold": 0.18,
                "device": "CPU (NumPy/OpenCV)",
                "change_detection": analysis
            }

        # ----------------------------------------------------
        # BRANCH 3: STRUCTURAL CHANGES (SIAMESE U-NET) - DEFAULT
        # ----------------------------------------------------
        else:
            print(f"\n[Processor] Running Structural Change Detection (Siamese U-Net)...")

            probability_map, prediction_mask = self._run_model(t1_effective_path, t2_effective_path)
            analysis, cleaned_mask = analyze_mask(prediction_mask)

            if output_mask_path is not None:
                self.save_mask(cleaned_mask, output_mask_path)
                self.create_change_overlay(t2_effective_path, cleaned_mask, overlay_path)

            result = {
                "channel_type": "STRUCTURAL_DL",
                "model": "Siamese U-Net (LEVIR-CD)",
                "threshold": self.threshold,
                "device": str(self.device),
                "probability_statistics": {
                    "min": round(float(probability_map.min()), 6),
                    "max": round(float(probability_map.max()), 6),
                    "mean": round(float(probability_map.mean()), 6)
                },
                "change_detection": analysis
            }

        # ----------------------------------------------------
        # GEOREFERENCED ENRICHMENT & METADATA (PS 2.2.6)
        # ----------------------------------------------------
        if geotiff_metadata and geotiff_metadata.get("is_geotiff"):
            transform_mat = geotiff_metadata.get("transform")
            crs_val = geotiff_metadata.get("crs")
            if transform_mat and crs_val and "regions" in analysis:
                analysis["regions"] = convert_regions_to_gps(
                    analysis["regions"],
                    transform_mat,
                    crs_val
                )

            result["geotiff_metadata"] = geotiff_metadata
            if geotiff_metadata.get("geojson_footprint"):
                result["feature_geojson"] = geotiff_metadata["geojson_footprint"]

        if is_geo:
            if t1_preview_path and os.path.exists(t1_preview_path):
                result["t1_preview"] = t1_preview_path
            if t2_preview_path and os.path.exists(t2_preview_path):
                result["t2_preview"] = t2_preview_path

        if output_mask_path is not None:
            result["output_mask"] = output_mask_path
            result["overlay_image"] = overlay_path

        return result


# ============================================================
# STANDALONE TEST
# ============================================================

def main():
    print("==========================================")
    print(" GAGANDRISTHI V2 - MULTI-CHANNEL PROCESSOR TEST")
    print("==========================================")

    t1_path = os.path.join(PROCESSING_ROOT, "test_images", "T1.jpeg")
    t2_path = os.path.join(PROCESSING_ROOT, "test_images", "T2.jpeg")

    processor = ChangeProcessor()

    for ch in ["structural", "vegetation", "pixel_diff"]:
        print(f"\nTesting channel: {ch.upper()}...")
        out_mask = os.path.join(PROCESSING_ROOT, "test_images", f"test_mask_{ch}.png")
        res = processor.process(t1_path, t2_path, output_mask_path=out_mask, channel_type=ch)
        print(f"[OK] Channel {ch}: change={res['change_detection']['change_percentage']}%, regions={res['change_detection']['number_of_regions']}, severity={res['change_detection']['severity']}")


if __name__ == "__main__":
    main()