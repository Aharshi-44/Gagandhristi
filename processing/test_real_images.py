import os
import torch
import numpy as np
from PIL import Image

from models.siamese_unet import SiameseUNet


# ============================================================
# FILE PATHS
# ============================================================

MODEL_PATH = "weights/siamese_unet_levir_cd.pth"

T1_PATH = "test_images/T1.jpeg"
T2_PATH = "test_images/T2.jpeg"
LABEL_PATH = "test_images/Label.jpeg"

OUTPUT_MASK = "test_images/predicted_mask.png"


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("==========================================")
print(" GAGANDRISTHI V2 - REAL IMAGE TEST")
print("==========================================")

print("Device:", device)

if torch.cuda.is_available():
    print(
        "GPU:",
        torch.cuda.get_device_name(0)
    )


# ============================================================
# CHECK FILES
# ============================================================

print("\nChecking files...")

files = [
    MODEL_PATH,
    T1_PATH,
    T2_PATH,
    LABEL_PATH
]

for path in files:

    if not os.path.exists(path):

        raise FileNotFoundError(
            f"\nFile not found:\n{path}"
        )

    print("✓", path)


# ============================================================
# LOAD RGB IMAGE
# ============================================================

def load_image(path):

    image = Image.open(path).convert("RGB")

    print(
        f"\nLoaded: {path}"
    )

    print(
        "Original size:",
        image.size
    )

    image = np.array(
        image
    ).astype(
        np.float32
    )

    # --------------------------------------------------------
    # Convert 0-255 → 0-1
    # --------------------------------------------------------

    image = image / 255.0

    # --------------------------------------------------------
    # HWC → CHW
    # --------------------------------------------------------

    image = np.transpose(
        image,
        (2, 0, 1)
    )

    # --------------------------------------------------------
    # Add batch dimension
    # --------------------------------------------------------

    image = torch.from_numpy(
        image
    ).unsqueeze(0)

    return image


# ============================================================
# LOAD LABEL
# ============================================================

def load_label(path):

    label = Image.open(
        path
    ).convert("L")

    print(
        f"\nLoaded label: {path}"
    )

    print(
        "Label size:",
        label.size
    )

    label = np.array(
        label
    )

    # --------------------------------------------------------
    # Convert label to binary
    #
    # Black = 0 = no change
    # White = 1 = change
    # --------------------------------------------------------

    label = (
        label > 127
    ).astype(
        np.uint8
    )

    return label


# ============================================================
# METRICS
# ============================================================

def calculate_metrics(
    prediction,
    ground_truth
):

    prediction = prediction.astype(
        bool
    )

    ground_truth = ground_truth.astype(
        bool
    )

    # --------------------------------------------------------
    # True Positive
    # --------------------------------------------------------

    tp = np.logical_and(
        prediction,
        ground_truth
    ).sum()

    # --------------------------------------------------------
    # False Positive
    # --------------------------------------------------------

    fp = np.logical_and(
        prediction,
        ~ground_truth
    ).sum()

    # --------------------------------------------------------
    # False Negative
    # --------------------------------------------------------

    fn = np.logical_and(
        ~prediction,
        ground_truth
    ).sum()

    # --------------------------------------------------------
    # IoU
    # --------------------------------------------------------

    union = np.logical_or(
        prediction,
        ground_truth
    ).sum()

    if union > 0:

        iou = tp / union

    else:

        iou = 1.0

    # --------------------------------------------------------
    # Dice / F1
    # --------------------------------------------------------

    total = (
        prediction.sum()
        +
        ground_truth.sum()
    )

    if total > 0:

        dice = (
            2 * tp / total
        )

    else:

        dice = 1.0

    # --------------------------------------------------------
    # Precision
    # --------------------------------------------------------

    if (tp + fp) > 0:

        precision = (
            tp /
            (tp + fp)
        )

    else:

        precision = 0.0

    # --------------------------------------------------------
    # Recall
    # --------------------------------------------------------

    if (tp + fn) > 0:

        recall = (
            tp /
            (tp + fn)
        )

    else:

        recall = 0.0

    return (
        iou,
        dice,
        precision,
        recall
    )


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # LOAD MODEL
    # ========================================================

    print("\n------------------------------------------")
    print("Loading Siamese U-Net...")
    print("------------------------------------------")

    model = SiameseUNet(
        in_channels=3
    )

    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device
    )

    result = model.load_state_dict(
        checkpoint,
        strict=True
    )

    print(
        "Missing keys:",
        result.missing_keys
    )

    print(
        "Unexpected keys:",
        result.unexpected_keys
    )

    model = model.to(
        device
    )

    model.eval()

    print("✓ Model loaded successfully")


    # ========================================================
    # LOAD T1
    # ========================================================

    print("\n------------------------------------------")
    print("Loading T1...")
    print("------------------------------------------")

    image1 = load_image(
        T1_PATH
    )


    # ========================================================
    # LOAD T2
    # ========================================================

    print("\n------------------------------------------")
    print("Loading T2...")
    print("------------------------------------------")

    image2 = load_image(
        T2_PATH
    )


    # ========================================================
    # LOAD LABEL
    # ========================================================

    print("\n------------------------------------------")
    print("Loading Label...")
    print("------------------------------------------")

    label = load_label(
        LABEL_PATH
    )


    # ========================================================
    # PRINT INPUT SHAPES
    # ========================================================

    print("\n------------------------------------------")
    print("Input tensors")
    print("------------------------------------------")

    print(
        "T1:",
        image1.shape
    )

    print(
        "T2:",
        image2.shape
    )

    print(
        "Label:",
        label.shape
    )


    # ========================================================
    # MOVE TO GPU
    # ========================================================

    image1 = image1.to(
        device
    )

    image2 = image2.to(
        device
    )


    # ========================================================
    # RUN MODEL
    # ========================================================

    print("\n------------------------------------------")
    print("Running inference...")
    print("------------------------------------------")

    with torch.no_grad():

        output = model(
            image1,
            image2
        )

        # ----------------------------------------------------
        # Convert logits → probability
        # ----------------------------------------------------

        probability = torch.sigmoid(
            output
        )

        # ----------------------------------------------------
        # Probability statistics
        # ----------------------------------------------------

        print(
            "Probability MIN:",
            probability.min().item()
        )

        print(
            "Probability MAX:",
            probability.max().item()
        )

        print(
            "Probability MEAN:",
            probability.mean().item()
        )

        # ----------------------------------------------------
        # Threshold
        # ----------------------------------------------------

        prediction = (
            probability > 0.5
        ).float()


    # ========================================================
    # OUTPUT SHAPE
    # ========================================================

    print(
        "\nModel output:",
        output.shape
    )


    # ========================================================
    # CONVERT PREDICTION TO NUMPY
    # ========================================================

    prediction = (
        prediction
        .squeeze()
        .cpu()
        .numpy()
    )

    prediction = prediction.astype(
        np.uint8
    )


    # ========================================================
    # SAVE PREDICTED MASK
    # ========================================================

    prediction_image = (
        prediction * 255
    )

    Image.fromarray(
        prediction_image
    ).save(
        OUTPUT_MASK
    )

    print(
        "\n✓ Predicted mask saved:"
    )

    print(
        OUTPUT_MASK
    )


    # ========================================================
    # CALCULATE METRICS
    # ========================================================

    print("\n------------------------------------------")
    print("Calculating metrics...")
    print("------------------------------------------")

    (
        iou,
        dice,
        precision,
        recall
    ) = calculate_metrics(
        prediction,
        label
    )


    # ========================================================
    # CHANGE PERCENTAGE
    # ========================================================

    predicted_change = (
        prediction.mean()
        *
        100
    )

    ground_truth_change = (
        label.mean()
        *
        100
    )


    # ========================================================
    # RESULTS
    # ========================================================

    print("\n==========================================")
    print(" RESULTS")
    print("==========================================")

    print(
        f"IoU       : {iou:.6f}"
    )

    print(
        f"Dice / F1 : {dice:.6f}"
    )

    print(
        f"Precision : {precision:.6f}"
    )

    print(
        f"Recall    : {recall:.6f}"
    )

    print("\nChange percentage:")

    print(
        f"Predicted    : {predicted_change:.4f}%"
    )

    print(
        f"Ground Truth : {ground_truth_change:.4f}%"
    )

    print("==========================================")


# ============================================================
# START
# ============================================================

if __name__ == "__main__":

    main()