import os
import gc
import torch
import numpy as np

from PIL import Image

from models.siamese_unet import SiameseUNet


# ============================================================
# PATHS
# ============================================================

MODEL_PATH = "weights/siamese_unet_levir_cd.pth"

T1_PATH = "test_images/T1.jpeg"
T2_PATH = "test_images/T2.jpeg"
LABEL_PATH = "test_images/Label.jpeg"


# ============================================================
# DEVICE
# ============================================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

print("==============================================")
print(" GAGANDRISTHI V2 - MODEL DIAGNOSTIC")
print("==============================================")

print("Device:", device)

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))


# ============================================================
# LOAD IMAGE
# ============================================================

def read_rgb(path):

    image = Image.open(path).convert("RGB")

    print(f"Loaded {path}: {image.size}")

    image = np.asarray(
        image,
        dtype=np.float32
    )

    return image


# ============================================================
# LOAD LABEL
# ============================================================

def read_label(path):

    label = Image.open(path).convert("L")

    label = np.asarray(
        label,
        dtype=np.uint8
    )

    # Black = no change
    # White = change
    label = (label > 127).astype(np.uint8)

    return label


# ============================================================
# CONVERT IMAGE TO TENSOR
# ============================================================

def image_to_tensor(
    image,
    mode
):

    # --------------------------------------------------------
    # Resize to 256x256 if required
    # --------------------------------------------------------

    if mode == "resize_256":

        pil = Image.fromarray(
            image.astype(np.uint8)
        )

        pil = pil.resize(
            (256, 256),
            Image.Resampling.BILINEAR
        )

        image = np.asarray(
            pil,
            dtype=np.float32
        )

    # --------------------------------------------------------
    # Convert to 0-1
    # --------------------------------------------------------

    image = image / 255.0

    # --------------------------------------------------------
    # Normalization options
    # --------------------------------------------------------

    if mode == "zero_one":

        pass

    elif mode == "minus_one_one":

        image = image * 2.0 - 1.0

    elif mode == "imagenet":

        mean = np.array(
            [0.485, 0.456, 0.406],
            dtype=np.float32
        )

        std = np.array(
            [0.229, 0.224, 0.225],
            dtype=np.float32
        )

        image = (
            image - mean
        ) / std

    elif mode == "resize_256":

        # Resize only.
        # Keep 0-1 normalization.
        pass

    else:

        raise ValueError(
            f"Unknown mode: {mode}"
        )

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

    tensor = torch.from_numpy(
        image
    ).unsqueeze(0)

    return tensor


# ============================================================
# METRICS
# ============================================================

def metrics(
    prediction,
    ground_truth
):

    prediction = prediction.astype(bool)
    ground_truth = ground_truth.astype(bool)

    tp = np.logical_and(
        prediction,
        ground_truth
    ).sum()

    fp = np.logical_and(
        prediction,
        ~ground_truth
    ).sum()

    fn = np.logical_and(
        ~prediction,
        ground_truth
    ).sum()

    union = np.logical_or(
        prediction,
        ground_truth
    ).sum()

    # IoU
    if union > 0:
        iou = tp / union
    else:
        iou = 1.0

    # Dice
    denominator = (
        prediction.sum()
        +
        ground_truth.sum()
    )

    if denominator > 0:
        dice = 2 * tp / denominator
    else:
        dice = 1.0

    # Precision
    if tp + fp > 0:
        precision = tp / (tp + fp)
    else:
        precision = 0.0

    # Recall
    if tp + fn > 0:
        recall = tp / (tp + fn)
    else:
        recall = 0.0

    return (
        iou,
        dice,
        precision,
        recall
    )


# ============================================================
# THRESHOLD ANALYSIS
# ============================================================

def threshold_analysis(
    probability,
    label
):

    print("\n")
    print("==============================================")
    print(" THRESHOLD ANALYSIS")
    print("==============================================")

    thresholds = [
        0.05,
        0.10,
        0.15,
        0.20,
        0.25,
        0.30,
        0.35,
        0.40,
        0.45,
        0.50,
        0.55,
        0.60
    ]

    best_iou = -1
    best_threshold = None

    print(
        "\nThreshold | IoU      | Dice     | Precision | Recall | Change %"
    )

    print(
        "----------|----------|----------|-----------|--------|---------"
    )

    for threshold in thresholds:

        prediction = (
            probability > threshold
        ).astype(np.uint8)

        iou, dice, precision, recall = metrics(
            prediction,
            label
        )

        change_percent = (
            prediction.mean() * 100
        )

        print(
            f"{threshold:9.2f} | "
            f"{iou:8.5f} | "
            f"{dice:8.5f} | "
            f"{precision:9.5f} | "
            f"{recall:6.5f} | "
            f"{change_percent:7.4f}%"
        )

        if iou > best_iou:

            best_iou = iou
            best_threshold = threshold

    print("\nBest threshold according to IoU:")
    print("Threshold:", best_threshold)
    print("IoU:", best_iou)


# ============================================================
# RUN ONE PREPROCESSING MODE
# ============================================================

def run_mode(
    model,
    image1,
    image2,
    label,
    mode
):

    print("\n")
    print("==============================================")
    print(" PREPROCESSING MODE:", mode)
    print("==============================================")

    tensor1 = image_to_tensor(
        image1,
        mode
    )

    tensor2 = image_to_tensor(
        image2,
        mode
    )

    print("T1 tensor:", tensor1.shape)
    print("T2 tensor:", tensor2.shape)

    tensor1 = tensor1.to(device)
    tensor2 = tensor2.to(device)

    # --------------------------------------------------------
    # Inference
    # --------------------------------------------------------

    with torch.no_grad():

        output = model(
            tensor1,
            tensor2
        )

        probability = torch.sigmoid(
            output
        )

    probability = (
        probability
        .squeeze()
        .cpu()
        .numpy()
    )

    print(
        "\nProbability statistics:"
    )

    print(
        "MIN :",
        float(probability.min())
    )

    print(
        "MAX :",
        float(probability.max())
    )

    print(
        "MEAN:",
        float(probability.mean())
    )

    print(
        "MEDIAN:",
        float(np.median(probability))
    )

    # --------------------------------------------------------
    # If resized to 256, resize probability back to 1024
    # for comparison with the original label.
    # --------------------------------------------------------

    if probability.shape != label.shape:

        probability_pil = Image.fromarray(
            probability.astype(np.float32),
            mode="F"
        )

        probability_pil = probability_pil.resize(
            (label.shape[1], label.shape[0]),
            Image.Resampling.BILINEAR
        )

        probability = np.asarray(
            probability_pil,
            dtype=np.float32
        )

    # --------------------------------------------------------
    # Threshold analysis
    # --------------------------------------------------------

    threshold_analysis(
        probability,
        label
    )

    # --------------------------------------------------------
    # Save a 0.5 mask
    # --------------------------------------------------------

    prediction = (
        probability > 0.5
    ).astype(np.uint8)

    output_path = (
        f"test_images/"
        f"diagnostic_{mode}_mask.png"
    )

    Image.fromarray(
        prediction * 255
    ).save(
        output_path
    )

    print(
        "\nSaved mask:",
        output_path
    )

    # --------------------------------------------------------
    # Free GPU memory
    # --------------------------------------------------------

    del tensor1
    del tensor2
    del output
    del probability

    gc.collect()

    if torch.cuda.is_available():

        torch.cuda.empty_cache()


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Check files
    # --------------------------------------------------------

    for path in [
        MODEL_PATH,
        T1_PATH,
        T2_PATH,
        LABEL_PATH
    ]:

        if not os.path.exists(path):

            raise FileNotFoundError(
                f"File not found: {path}"
            )

    # --------------------------------------------------------
    # Load model
    # --------------------------------------------------------

    print("\nLoading model...")

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

    model = model.to(device)
    model.eval()

    print("✓ Model loaded")

    # --------------------------------------------------------
    # Load images
    # --------------------------------------------------------

    print("\nLoading images...")

    image1 = read_rgb(
        T1_PATH
    )

    image2 = read_rgb(
        T2_PATH
    )

    label = read_label(
        LABEL_PATH
    )

    print(
        "\nGround-truth change:",
        f"{label.mean() * 100:.4f}%"
    )

    # --------------------------------------------------------
    # Test different preprocessing methods
    # --------------------------------------------------------

    modes = [
        "zero_one",
        "minus_one_one",
        "imagenet",
        "resize_256"
    ]

    for mode in modes:

        run_mode(
            model,
            image1,
            image2,
            label,
            mode
        )

    # --------------------------------------------------------
    # Finish
    # --------------------------------------------------------

    print("\n")
    print("==============================================")
    print(" DIAGNOSTIC COMPLETE")
    print("==============================================")


if __name__ == "__main__":

    main()