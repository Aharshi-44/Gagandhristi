import cv2
import numpy as np
from inference.change_analysis import clean_mask, extract_regions, determine_severity


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_PIXEL_DIFF_THRESHOLD = 0.18
MIN_DIFF_REGION_AREA = 25


# ============================================================
# PIXEL-TO-PIXEL RADIOMETRIC CHANGE ANALYSIS
# ============================================================

def detect_pixel_diff_change(
    t1_image,
    t2_image,
    threshold=DEFAULT_PIXEL_DIFF_THRESHOLD,
    min_area=MIN_DIFF_REGION_AREA
):
    """
    Perform Change Vector Analysis (CVA) / Euclidean radiometric differencing
    between T1 and T2 images.

    Captures broad surface anomalies, vehicles, tire tracks, tents, and ground disturbance.

    Args:
        t1_image: numpy array (H, W, 3) in RGB
        t2_image: numpy array (H, W, 3) in RGB
        threshold: normalized intensity difference threshold in [0, 1] (default 0.18)
        min_area: minimum connected region area in pixels (default 25)

    Returns:
        dict containing binary change mask, region extraction, and telemetry.
    """
    # Normalize images to [0, 1] float32
    t1_f = t1_image.astype(np.float32) / 255.0
    t2_f = t2_image.astype(np.float32) / 255.0

    # Ensure identical dimensions
    if t1_f.shape != t2_f.shape:
        h, w = min(t1_f.shape[0], t2_f.shape[0]), min(t1_f.shape[1], t2_f.shape[1])
        t1_f = t1_f[:h, :w]
        t2_f = t2_f[:h, :w]

    # Euclidean color difference across RGB channels (Change Vector Analysis magnitude)
    diff = np.sqrt(np.mean((t2_f - t1_f) ** 2, axis=2))

    # Apply Gaussian smoothing to suppress sensor noise & registration jitter
    diff_smoothed = cv2.GaussianBlur(diff, (3, 3), 0.8)

    # Initial binary thresholding
    raw_mask = (diff_smoothed > threshold).astype(np.uint8)

    # Morphological opening (remove salt noise) followed by closing (solidify cohesive objects)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    morphed = cv2.morphologyEx(raw_mask, cv2.MORPH_OPEN, kernel)
    morphed = cv2.morphologyEx(morphed, cv2.MORPH_CLOSE, kernel)

    # Remove small noise clusters below minimum area
    cleaned_mask = clean_mask(morphed, min_area=min_area)

    # Extract individual regions
    regions = extract_regions(cleaned_mask, min_area=min_area)

    # Compute metrics
    total_pixels = cleaned_mask.size
    changed_pixels = int(np.count_nonzero(cleaned_mask))
    change_percentage = round((changed_pixels / total_pixels) * 100, 3)

    severity = determine_severity(change_percentage)

    return {
        "channel_type": "pixel_diff",
        "algorithm": "Radiometric Change Vector Analysis (CVA)",
        "mask": cleaned_mask,  # 0 or 1
        "change_percentage": change_percentage,
        "severity": severity,
        "total_regions": len(regions),
        "regions": regions,
        "raw_diff_magnitude": diff_smoothed
    }


# ============================================================
# CREATE AMBER/ORANGE TACTICAL ANOMALY OVERLAY
# ============================================================

def create_pixel_diff_overlay(
    t2_image_bgr,
    mask,
    alpha=0.45
):
    """
    Overlay pixel-to-pixel anomalies onto T2 image using an amber/orange tint
    (distinct from structural red and vegetation green).

    Args:
        t2_image_bgr: original T2 image in BGR
        mask: binary mask (0 or 1)
        alpha: transparency blending factor

    Returns:
        blended BGR image
    """
    overlay = t2_image_bgr.copy()

    # Amber / Orange color in BGR: [0, 140, 255]
    changed_indices = mask > 0
    overlay[changed_indices] = [0, 140, 255]

    blended = t2_image_bgr.copy()
    blended[changed_indices] = cv2.addWeighted(
        t2_image_bgr[changed_indices],
        1.0 - alpha,
        overlay[changed_indices],
        alpha,
        0
    )

    return blended
