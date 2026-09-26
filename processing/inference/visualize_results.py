import os
import sys

import cv2
import numpy as np
from PIL import Image


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# PATHS
# ============================================================

T1_PATH = "test_images/T1.jpeg"
T2_PATH = "test_images/T2.jpeg"
LABEL_PATH = "test_images/Label.jpeg"
PREDICTION_PATH = "test_images/predicted_mask_v2.png"

OUTPUT_PATH = "test_images/visual_comparison.png"


# ============================================================
# LOAD RGB IMAGE
# ============================================================

def load_rgb(path):

    image = cv2.imread(path)

    if image is None:
        raise FileNotFoundError(
            f"Could not load image: {path}"
        )

    # OpenCV BGR → RGB
    image = cv2.cvtColor(
        image,
        cv2.COLOR_BGR2RGB
    )

    return image


# ============================================================
# LOAD MASK
# ============================================================

def load_mask(path):

    mask = cv2.imread(
        path,
        cv2.IMREAD_GRAYSCALE
    )

    if mask is None:
        raise FileNotFoundError(
            f"Could not load mask: {path}"
        )

    return (
        mask > 127
    ).astype(
        np.uint8
    )


# ============================================================
# RESIZE IMAGE
# ============================================================

def resize_to(
    image,
    width,
    height
):

    return cv2.resize(
        image,
        (width, height),
        interpolation=cv2.INTER_AREA
    )


# ============================================================
# CREATE MASK VISUALIZATION
# ============================================================

def mask_to_rgb(mask):

    result = np.zeros(
        (
            mask.shape[0],
            mask.shape[1],
            3
        ),
        dtype=np.uint8
    )

    # White = change
    result[mask == 1] = [
        255,
        255,
        255
    ]

    return result


# ============================================================
# CREATE COMPARISON OVERLAY
# ============================================================

def create_overlay(
    label,
    prediction
):

    height, width = label.shape

    overlay = np.zeros(
        (
            height,
            width,
            3
        ),
        dtype=np.uint8
    )

    # --------------------------------------------------------
    # True Positive
    #
    # Prediction = 1
    # Label      = 1
    #
    # White
    # --------------------------------------------------------

    true_positive = (
        (prediction == 1)
        &
        (label == 1)
    )

    overlay[
        true_positive
    ] = [
        255,
        255,
        255
    ]

    # --------------------------------------------------------
    # False Positive
    #
    # Prediction = 1
    # Label      = 0
    #
    # Red
    # --------------------------------------------------------

    false_positive = (
        (prediction == 1)
        &
        (label == 0)
    )

    overlay[
        false_positive
    ] = [
        255,
        0,
        0
    ]

    # --------------------------------------------------------
    # False Negative
    #
    # Prediction = 0
    # Label      = 1
    #
    # Blue
    # --------------------------------------------------------

    false_negative = (
        (prediction == 0)
        &
        (label == 1)
    )

    overlay[
        false_negative
    ] = [
        0,
        0,
        255
    ]

    return overlay


# ============================================================
# ADD TITLE
# ============================================================

def add_title(
    image,
    title
):

    image = image.copy()

    cv2.rectangle(
        image,
        (0, 0),
        (image.shape[1], 45),
        (0, 0, 0),
        -1
    )

    cv2.putText(
        image,
        title,
        (15, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    return image


# ============================================================
# CREATE LEGEND
# ============================================================

def create_legend(
    width
):

    height = 70

    legend = np.zeros(
        (
            height,
            width,
            3
        ),
        dtype=np.uint8
    )

    # True Positive
    cv2.rectangle(
        legend,
        (20, 20),
        (40, 40),
        (255, 255, 255),
        -1
    )

    cv2.putText(
        legend,
        "Correct prediction",
        (50, 37),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    # False Positive
    cv2.rectangle(
        legend,
        (230, 20),
        (250, 40),
        (255, 0, 0),
        -1
    )

    cv2.putText(
        legend,
        "False positive",
        (260, 37),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    # False Negative
    cv2.rectangle(
        legend,
        (420, 20),
        (440, 40),
        (0, 0, 255),
        -1
    )

    cv2.putText(
        legend,
        "Missed change",
        (450, 37),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA
    )

    return legend


# ============================================================
# MAIN
# ============================================================

def main():

    print("==========================================")
    print(" VISUAL CHANGE DETECTION ANALYSIS")
    print("==========================================")

    # --------------------------------------------------------
    # Load images
    # --------------------------------------------------------

    print("\nLoading images...")

    t1 = load_rgb(
        T1_PATH
    )

    t2 = load_rgb(
        T2_PATH
    )

    label = load_mask(
        LABEL_PATH
    )

    prediction = load_mask(
        PREDICTION_PATH
    )

    # --------------------------------------------------------
    # Verify dimensions
    # --------------------------------------------------------

    print(
        "T1:",
        t1.shape
    )

    print(
        "T2:",
        t2.shape
    )

    print(
        "Label:",
        label.shape
    )

    print(
        "Prediction:",
        prediction.shape
    )

    if label.shape != prediction.shape:

        raise ValueError(
            "Label and prediction dimensions do not match."
        )

    # --------------------------------------------------------
    # Calculate basic statistics
    # --------------------------------------------------------

    label_pixels = np.count_nonzero(
        label
    )

    prediction_pixels = np.count_nonzero(
        prediction
    )

    true_positive = np.logical_and(
        label == 1,
        prediction == 1
    ).sum()

    false_positive = np.logical_and(
        label == 0,
        prediction == 1
    ).sum()

    false_negative = np.logical_and(
        label == 1,
        prediction == 0
    ).sum()

    print("\nStatistics:")

    print(
        "Ground-truth changed pixels:",
        label_pixels
    )

    print(
        "Predicted changed pixels:",
        prediction_pixels
    )

    print(
        "Correctly detected pixels:",
        true_positive
    )

    print(
        "False positive pixels:",
        false_positive
    )

    print(
        "Missed change pixels:",
        false_negative
    )

    # --------------------------------------------------------
    # Create mask images
    # --------------------------------------------------------

    label_visual = mask_to_rgb(
        label
    )

    prediction_visual = mask_to_rgb(
        prediction
    )

    # --------------------------------------------------------
    # Create overlay
    # --------------------------------------------------------

    overlay = create_overlay(
        label,
        prediction
    )

    # --------------------------------------------------------
    # Resize all panels
    # --------------------------------------------------------

    panel_width = 512
    panel_height = 512

    t1 = resize_to(
        t1,
        panel_width,
        panel_height
    )

    t2 = resize_to(
        t2,
        panel_width,
        panel_height
    )

    label_visual = resize_to(
        label_visual,
        panel_width,
        panel_height
    )

    prediction_visual = resize_to(
        prediction_visual,
        panel_width,
        panel_height
    )

    overlay = resize_to(
        overlay,
        panel_width,
        panel_height
    )

    # --------------------------------------------------------
    # Add titles
    # --------------------------------------------------------

    t1 = add_title(
        t1,
        "T1 - Earlier Image"
    )

    t2 = add_title(
        t2,
        "T2 - Later Image"
    )

    label_visual = add_title(
        label_visual,
        "Ground Truth Label"
    )

    prediction_visual = add_title(
        prediction_visual,
        "Model Prediction"
    )

    overlay = add_title(
        overlay,
        "Prediction vs Ground Truth"
    )

    # --------------------------------------------------------
    # Create top row
    # --------------------------------------------------------

    top_row = np.hstack(
        [
            t1,
            t2
        ]
    )

    # --------------------------------------------------------
    # Create second row
    # --------------------------------------------------------

    second_row = np.hstack(
        [
            label_visual,
            prediction_visual
        ]
    )

    # --------------------------------------------------------
    # Bottom overlay
    # --------------------------------------------------------

    legend = create_legend(
        panel_width
    )

    bottom = np.vstack(
        [
            overlay,
            legend
        ]
    )

    # --------------------------------------------------------
    # Make bottom same width
    # --------------------------------------------------------

    bottom_width = bottom.shape[1]

    target_width = top_row.shape[1]

    if bottom_width < target_width:

        padding = np.zeros(
            (
                bottom.shape[0],
                target_width - bottom_width,
                3
            ),
            dtype=np.uint8
        )

        bottom = np.hstack(
            [
                bottom,
                padding
            ]
        )

    # --------------------------------------------------------
    # Final comparison image
    # --------------------------------------------------------

    comparison = np.vstack(
        [
            top_row,
            second_row,
            bottom
        ]
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    cv2.imwrite(
        OUTPUT_PATH,
        cv2.cvtColor(
            comparison,
            cv2.COLOR_RGB2BGR
        )
    )

    print(
        "\n✓ Visual comparison saved:"
    )

    print(
        OUTPUT_PATH
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()