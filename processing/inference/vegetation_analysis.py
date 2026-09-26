import cv2
import numpy as np
from inference.change_analysis import clean_mask, extract_regions, determine_severity


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_VEG_THRESHOLD = 0.12
MIN_VEG_REGION_AREA = 20


# ============================================================
# VEGETATION INDEX COMPUTATION
# ============================================================

def compute_vegetation_index(image):
    """
    Compute vegetation index for an input image (H, W, C).
    
    - If image has 4 channels (RGB + NIR): computes NDVI = (NIR - Red) / (NIR + Red)
    - If image has 3 channels (RGB in RGB order):
      computes VARI = (Green - Red) / (Green + Red - Blue + 1e-6)
      
    Returns:
        veg_index: 2D numpy array with values in [-1.0, 1.0]
        index_name: str ("NDVI" or "VARI")
    """
    img_float = image.astype(np.float32) / 255.0

    if img_float.ndim == 3 and img_float.shape[2] >= 4:
        # 4-band: Red=0, Green=1, Blue=2, NIR=3
        red = img_float[:, :, 0]
        nir = img_float[:, :, 3]
        denominator = nir + red + 1e-7
        ndvi = (nir - red) / denominator
        return np.clip(ndvi, -1.0, 1.0), "NDVI"
    
    elif img_float.ndim == 3 and img_float.shape[2] == 3:
        # 3-band RGB: Red=0, Green=1, Blue=2
        red = img_float[:, :, 0]
        green = img_float[:, :, 1]
        blue = img_float[:, :, 2]
        
        # VARI: Visible Atmospherically Resistant Index
        denominator = green + red - blue + 1e-7
        denominator = np.where(np.abs(denominator) < 1e-5, 1e-5, denominator)
        vari = (green - red) / denominator
        
        # Also compute Green Leaf Index (GLI) to stabilize VARI in shadowy areas
        gli_denom = 2 * green + red + blue + 1e-7
        gli = (2 * green - red - blue) / gli_denom
        
        # Blend stabilized VARI
        combined = 0.7 * vari + 0.3 * gli
        return np.clip(combined, -1.0, 1.0), "VARI (RGB NDVI)"
    
    else:
        # Single channel grayscale fallback
        return np.zeros((image.shape[0], image.shape[1]), dtype=np.float32), "NONE"


# ============================================================
# VEGETATION CHANGE DETECTION PIPELINE
# ============================================================

def detect_vegetation_change(
    t1_image,
    t2_image,
    threshold=DEFAULT_VEG_THRESHOLD,
    min_area=MIN_VEG_REGION_AREA
):
    """
    Detect multi-temporal vegetation changes between T1 and T2.

    Identifies:
    - Vegetation Loss (Clearance/Deforestation): Delta < -threshold
    - Vegetation Gain (Regrowth/Greening): Delta > +threshold

    Args:
        t1_image: numpy array (H, W, 3) in RGB
        t2_image: numpy array (H, W, 3) in RGB
        threshold: sensitivity threshold for index difference (default 0.12)
        min_area: minimum region size in pixels to filter noise (default 20)

    Returns:
        dict containing binary masks, regions, severity, and stats.
    """
    v1, idx1_name = compute_vegetation_index(t1_image)
    v2, idx2_name = compute_vegetation_index(t2_image)

    # Calculate delta: positive means greening, negative means clearing
    delta_veg = v2 - v1

    # Apply Gaussian smoothing to delta to suppress fine pixel noise
    smoothed_delta = cv2.GaussianBlur(delta_veg, (5, 5), 1.0)

    # Vegetation Loss / Clearance mask (primary defense threat)
    raw_loss_mask = (smoothed_delta < -threshold).astype(np.uint8)

    # Vegetation Gain / Regrowth mask
    raw_gain_mask = (smoothed_delta > threshold).astype(np.uint8)

    # Clean noise using 8-connected components
    clean_loss = clean_mask(raw_loss_mask, min_area=min_area)
    clean_gain = clean_mask(raw_gain_mask, min_area=min_area)

    # Extract clearance regions (for alerts and geospatial tracking)
    loss_regions = extract_regions(clean_loss, min_area=min_area)
    gain_regions = extract_regions(clean_gain, min_area=min_area)

    # Metrics
    total_pixels = clean_loss.size
    loss_pixels = int(np.count_nonzero(clean_loss))
    gain_pixels = int(np.count_nonzero(clean_gain))

    loss_percentage = round((loss_pixels / total_pixels) * 100, 3)
    gain_percentage = round((gain_pixels / total_pixels) * 100, 3)

    severity = determine_severity(loss_percentage)

    return {
        "channel_type": "vegetation",
        "index_used": idx2_name,
        "loss_mask": clean_loss,  # 0 or 1
        "gain_mask": clean_gain,  # 0 or 1
        "loss_percentage": loss_percentage,
        "gain_percentage": gain_percentage,
        "change_percentage": loss_percentage,  # Primary indicator for alert system
        "severity": severity,
        "total_regions": len(loss_regions),
        "regions": loss_regions,
        "gain_regions_count": len(gain_regions),
        "delta_veg": delta_veg
    }


# ============================================================
# CREATE MULTI-COLOR VEGETATION OVERLAY
# ============================================================

def create_vegetation_overlay(
    t2_image_bgr,
    loss_mask,
    gain_mask=None,
    alpha=0.45
):
    """
    Overlay vegetation changes onto T2 image.
    
    Color coding:
    - Red (0, 0, 220 in BGR): Vegetation clearance / Deforestation
    - Green (0, 200, 0 in BGR): Vegetation regrowth / Greening

    Args:
        t2_image_bgr: original T2 image in BGR
        loss_mask: binary mask (0 or 1) of clearance
        gain_mask: optional binary mask (0 or 1) of regrowth
        alpha: transparency blending factor

    Returns:
        blended BGR image
    """
    overlay = t2_image_bgr.copy()

    # Apply red overlay for vegetation clearance
    loss_indices = loss_mask > 0
    overlay[loss_indices] = [0, 0, 220]

    # Apply green overlay for vegetation regrowth
    if gain_mask is not None:
        gain_indices = gain_mask > 0
        overlay[gain_indices] = [0, 200, 0]

    # Alpha blend only where changes occurred
    active_mask = loss_indices
    if gain_mask is not None:
        active_mask = np.logical_or(loss_indices, gain_mask > 0)

    blended = t2_image_bgr.copy()
    blended[active_mask] = cv2.addWeighted(
        t2_image_bgr[active_mask],
        1.0 - alpha,
        overlay[active_mask],
        alpha,
        0
    )

    return blended
