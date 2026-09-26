import os
import sys

# pyrefly: ignore [missing-import]
import torch
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
    sys.path.insert(
        0,
        PROJECT_ROOT
    )


# ============================================================
# PROJECT IMPORTS
# ============================================================

from models.siamese_unet import SiameseUNet
from preprocessing.preprocess import load_and_preprocess

# ============================================================
# MODEL CONFIGURATION
# ============================================================

MODEL_PATH = os.path.join(
    "weights",
    "siamese_unet_levir_cd.pth"
)

DEFAULT_THRESHOLD = 0.25


# ============================================================
# DEVICE
# ============================================================

DEVICE = torch.device(
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ============================================================
# MODEL LOADER
# ============================================================

def load_model(
    model_path=MODEL_PATH
):
    """
    Load the Siamese U-Net and its trained weights.
    """

    print("Loading Siamese U-Net...")

    model = SiameseUNet(
        in_channels=3
    )

    checkpoint = torch.load(
        model_path,
        map_location=DEVICE
    )

    model.load_state_dict(
        checkpoint,
        strict=True
    )

    model = model.to(
        DEVICE
    )

    model.eval()

    print(
        "Model loaded on:",
        DEVICE
    )

    return model


# ============================================================
# PREDICTION
# ============================================================

def predict(
    model,
    t1_path,
    t2_path,
    threshold=DEFAULT_THRESHOLD
):
    """
    Run change detection on a T1/T2 image pair.

    Returns:

        probability_map
        prediction_mask
    """

    # --------------------------------------------------------
    # Load and preprocess T1
    # --------------------------------------------------------

    image1 = load_and_preprocess(
        t1_path
    )

    # --------------------------------------------------------
    # Load and preprocess T2
    # --------------------------------------------------------

    image2 = load_and_preprocess(
        t2_path
    )

    # --------------------------------------------------------
    # Check dimensions
    # --------------------------------------------------------

    if image1.shape != image2.shape:

        raise ValueError(
            "T1 and T2 must have identical dimensions. "
            f"T1={image1.shape}, T2={image2.shape}"
        )

    # --------------------------------------------------------
    # Move to GPU / CPU
    # --------------------------------------------------------

    image1 = image1.to(
        DEVICE
    )

    image2 = image2.to(
        DEVICE
    )

    # --------------------------------------------------------
    # Inference
    # --------------------------------------------------------

    with torch.no_grad():

        logits = model(
            image1,
            image2
        )

        probability = torch.sigmoid(
            logits
        )

    # --------------------------------------------------------
    # Convert to NumPy
    # --------------------------------------------------------

    probability_map = (
        probability
        .squeeze()
        .cpu()
        .numpy()
    )

    # --------------------------------------------------------
    # Binary prediction
    # --------------------------------------------------------

    prediction_mask = (
        probability_map >= threshold
    ).astype(
        np.uint8
    )

    return (
        probability_map,
        prediction_mask
    )


# ============================================================
# SAVE MASK
# ============================================================

def save_mask(
    prediction_mask,
    output_path
):
    """
    Save a binary prediction mask.

    Black  = no change
    White  = change
    """

    mask = (
        prediction_mask * 255
    ).astype(
        np.uint8
    )

    Image.fromarray(
        mask
    ).save(
        output_path
    )

    print(
        "Prediction saved:",
        output_path
    )


# ============================================================
# MAIN TEST
# ============================================================

def main():

    T1_PATH = os.path.join(
        "test_images",
        "T1.jpeg"
    )

    T2_PATH = os.path.join(
        "test_images",
        "T2.jpeg"
    )

    OUTPUT_PATH = os.path.join(
        "test_images",
        "predicted_mask_v2.png"
    )

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    for path in [
        MODEL_PATH,
        T1_PATH,
        T2_PATH
    ]:

        if not os.path.exists(path):

            raise FileNotFoundError(
                f"File not found: {path}"
            )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    model = load_model()

    # --------------------------------------------------------
    # Run prediction
    # --------------------------------------------------------

    print("\nRunning change detection...")

    probability_map, prediction_mask = predict(
        model,
        T1_PATH,
        T2_PATH,
        threshold=DEFAULT_THRESHOLD
    )

    # --------------------------------------------------------
    # Statistics
    # --------------------------------------------------------

    print("\nPrediction statistics:")

    print(
        "Probability MIN:",
        float(probability_map.min())
    )

    print(
        "Probability MAX:",
        float(probability_map.max())
    )

    print(
        "Probability MEAN:",
        float(probability_map.mean())
    )

    print(
        "Threshold:",
        DEFAULT_THRESHOLD
    )

    change_percentage = (
        prediction_mask.mean()
        *
        100
    )

    print(
        f"Predicted change: "
        f"{change_percentage:.4f}%"
    )

    # --------------------------------------------------------
    # Save result
    # --------------------------------------------------------

    save_mask(
        prediction_mask,
        OUTPUT_PATH
    )


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()