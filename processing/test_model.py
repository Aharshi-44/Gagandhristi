import torch

from models.siamese_unet import SiameseUNet


MODEL_PATH = "weights/siamese_unet_levir_cd.pth"


def main():

    device = torch.device(
        "cuda" if torch.cuda.is_available() else "cpu"
    )

    print("Device:", device)

    # Create model
    model = SiameseUNet(
        in_channels=3
    )

    # Load checkpoint
    checkpoint = torch.load(
        MODEL_PATH,
        map_location=device
    )

    # Load weights
    result = model.load_state_dict(
        checkpoint,
        strict=True
    )

    print("Missing keys:", result.missing_keys)
    print("Unexpected keys:", result.unexpected_keys)

    model = model.to(device)
    model.eval()

    # Dummy RGB images
    image1 = torch.randn(
        1, 3, 256, 256
    ).to(device)

    image2 = torch.randn(
        1, 3, 256, 256
    ).to(device)

    # Inference
    with torch.no_grad():

        output = model(
            image1,
            image2
        )

    print("Input 1:", image1.shape)
    print("Input 2:", image2.shape)
    print("Output :", output.shape)


if __name__ == "__main__":
    main()