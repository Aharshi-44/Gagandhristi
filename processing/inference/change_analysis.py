import cv2
import numpy as np


# ============================================================
# CONFIGURATION
# ============================================================

# Minimum number of pixels required for a region
# to be considered a meaningful change.
MIN_REGION_AREA = 20


# ============================================================
# LOAD MASK
# ============================================================

def load_mask(mask_path):
    """
    Load a binary change mask.

    Black = no change
    White = change

    Returns:
        numpy array containing 0 and 1.
    """

    mask = cv2.imread(
        mask_path,
        cv2.IMREAD_GRAYSCALE
    )

    if mask is None:

        raise FileNotFoundError(
            f"Could not load mask: {mask_path}"
        )

    # Convert grayscale mask to binary
    binary_mask = (
        mask > 127
    ).astype(
        np.uint8
    )

    return binary_mask


# ============================================================
# REMOVE SMALL NOISE
# ============================================================

def clean_mask(
    mask,
    min_area=MIN_REGION_AREA
):
    """
    Remove very small isolated regions.

    This helps eliminate small prediction noise.
    """

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask,
        connectivity=8
    )

    cleaned = np.zeros_like(
        mask
    )

    for label_id in range(
        1,
        num_labels
    ):

        area = stats[
            label_id,
            cv2.CC_STAT_AREA
        ]

        if area >= min_area:

            cleaned[
                labels == label_id
            ] = 1

    return cleaned


# ============================================================
# EXTRACT CHANGE REGIONS
# ============================================================

def extract_regions(
    mask,
    min_area=MIN_REGION_AREA
):
    """
    Extract individual connected change regions.

    Returns:
        list of region dictionaries.
    """

    num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask,
        connectivity=8
    )

    regions = []

    region_id = 1

    for label_id in range(
        1,
        num_labels
    ):

        x = stats[
            label_id,
            cv2.CC_STAT_LEFT
        ]

        y = stats[
            label_id,
            cv2.CC_STAT_TOP
        ]

        width = stats[
            label_id,
            cv2.CC_STAT_WIDTH
        ]

        height = stats[
            label_id,
            cv2.CC_STAT_HEIGHT
        ]

        area = stats[
            label_id,
            cv2.CC_STAT_AREA
        ]

        # Ignore tiny regions
        if area < min_area:
            continue

        centroid_x = centroids[
            label_id
        ][0]

        centroid_y = centroids[
            label_id
        ][1]

        regions.append(
            {
                "region_id": region_id,

                "area_pixels": int(
                    area
                ),

                "bounding_box": {
                    "x": int(x),
                    "y": int(y),
                    "width": int(width),
                    "height": int(height)
                },

                "centroid": {
                    "x": round(
                        float(centroid_x),
                        2
                    ),

                    "y": round(
                        float(centroid_y),
                        2
                    )
                }
            }
        )

        region_id += 1

    return regions


# ============================================================
# CALCULATE CHANGE PERCENTAGE
# ============================================================

def calculate_change_percentage(
    mask
):
    """
    Calculate percentage of image classified as changed.
    """

    changed_pixels = np.count_nonzero(
        mask
    )

    total_pixels = mask.size

    percentage = (
        changed_pixels /
        total_pixels
    ) * 100

    return percentage


# ============================================================
# DETERMINE SEVERITY
# ============================================================

def determine_severity(
    change_percentage
):
    """
    Convert changed-area percentage into
    a simple severity level.

    These thresholds are initial engineering
    thresholds, NOT scientifically validated
    thresholds.
    """

    if change_percentage < 0.10:

        return "LOW"

    elif change_percentage < 1.00:

        return "MEDIUM"

    elif change_percentage < 3.00:

        return "HIGH"

    else:

        return "CRITICAL"


# ============================================================
# COMPLETE ANALYSIS
# ============================================================

def analyze_mask(
    mask,
    min_area=MIN_REGION_AREA
):
    """
    Analyze a binary change mask.

    Returns:
        dictionary containing change information.
    """

    # --------------------------------------------------------
    # Clean mask
    # --------------------------------------------------------

    cleaned_mask = clean_mask(
        mask,
        min_area
    )

    # --------------------------------------------------------
    # Calculate percentage
    # --------------------------------------------------------

    change_percentage = calculate_change_percentage(
        cleaned_mask
    )

    # --------------------------------------------------------
    # Determine whether change exists
    # --------------------------------------------------------

    change_detected = (
        change_percentage > 0
    )

    # --------------------------------------------------------
    # Extract regions
    # --------------------------------------------------------

    regions = extract_regions(
        cleaned_mask,
        min_area
    )

    # --------------------------------------------------------
    # Severity
    # --------------------------------------------------------

    severity = determine_severity(
        change_percentage
    )

    # --------------------------------------------------------
    # Result
    # --------------------------------------------------------

    result = {

        "change_detected": bool(
            change_detected
        ),

        "change_percentage": round(
            float(change_percentage),
            4
        ),

        "severity": severity,

        "number_of_regions": len(
            regions
        ),

        "regions": regions
    }

    return (
        result,
        cleaned_mask
    )


# ============================================================
# SAVE CLEANED MASK
# ============================================================

def save_mask(
    mask,
    output_path
):
    """
    Save a binary mask as PNG.
    """

    output = (
        mask * 255
    ).astype(
        np.uint8
    )

    cv2.imwrite(
        output_path,
        output
    )


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    import json

    MASK_PATH = (
        "test_images/"
        "predicted_mask_v2.png"
    )

    OUTPUT_PATH = (
        "test_images/"
        "cleaned_mask.png"
    )

    print("Loading predicted mask...")

    mask = load_mask(
        MASK_PATH
    )

    print(
        "Mask shape:",
        mask.shape
    )

    print(
        "Original changed pixels:",
        int(mask.sum())
    )

    print(
        "Original change:",
        f"{calculate_change_percentage(mask):.4f}%"
    )

    # --------------------------------------------------------
    # Analyze
    # --------------------------------------------------------

    result, cleaned_mask = analyze_mask(
        mask
    )

    # --------------------------------------------------------
    # Save cleaned mask
    # --------------------------------------------------------

    save_mask(
        cleaned_mask,
        OUTPUT_PATH
    )

    # --------------------------------------------------------
    # Print JSON result
    # --------------------------------------------------------

    print("\n==========================================")
    print(" CHANGE ANALYSIS")
    print("==========================================")

    print(
        json.dumps(
            result,
            indent=4
        )
    )

    print(
        "\nCleaned mask saved:",
        OUTPUT_PATH
    )