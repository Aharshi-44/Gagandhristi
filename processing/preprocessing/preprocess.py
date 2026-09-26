import numpy as np
import torch
from PIL import Image


def load_rgb_image(image_path):
    """
    Load an RGB image from disk.

    Returns:
        numpy array with shape:
        (H, W, 3)
    """

    image = Image.open(image_path).convert("RGB")

    image = np.asarray(
        image,
        dtype=np.float32
    )

    return image


def preprocess_image(image):
    """
    Preprocess an RGB image for the Siamese U-Net.

    Current verified preprocessing:

        uint8 0-255
             ↓
        float32
             ↓
        0-1
             ↓
        -1 to +1

    Returns:
        PyTorch tensor with shape:
        (1, 3, H, W)
    """

    # ------------------------------------------------------
    # 0-255 → 0-1
    # ------------------------------------------------------

    image = image / 255.0

    # ------------------------------------------------------
    # 0-1 → -1 to +1
    # ------------------------------------------------------

    image = image * 2.0 - 1.0

    # ------------------------------------------------------
    # HWC → CHW
    # ------------------------------------------------------

    image = np.transpose(
        image,
        (2, 0, 1)
    )

    # ------------------------------------------------------
    # NumPy → PyTorch
    # ------------------------------------------------------

    tensor = torch.from_numpy(
        image
    ).float()

    # ------------------------------------------------------
    # Add batch dimension
    # ------------------------------------------------------

    tensor = tensor.unsqueeze(0)

    return tensor


def load_and_preprocess(image_path):
    """
    Convenience function that loads and preprocesses
    an RGB image.
    """

    image = load_rgb_image(
        image_path
    )

    tensor = preprocess_image(
        image
    )

    return tensor