import torch
import torch.nn as nn
import torch.nn.functional as F


class ConvBlock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()

        self.conv = nn.Sequential(
            nn.Conv2d(
                in_channels,
                out_channels,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),

            nn.Conv2d(
                out_channels,
                out_channels,
                kernel_size=3,
                padding=1
            ),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        return self.conv(x)


class SiameseUNet(nn.Module):

    def __init__(self, in_channels=3):
        super().__init__()

        # -------------------------
        # Encoder 1
        # -------------------------

        self.enc1_conv1 = ConvBlock(in_channels, 64)
        self.enc1_conv2 = ConvBlock(64, 128)
        self.enc1_conv3 = ConvBlock(128, 256)
        self.enc1_conv4 = ConvBlock(256, 512)

        # -------------------------
        # Encoder 2
        # -------------------------

        self.enc2_conv1 = ConvBlock(in_channels, 64)
        self.enc2_conv2 = ConvBlock(64, 128)
        self.enc2_conv3 = ConvBlock(128, 256)
        self.enc2_conv4 = ConvBlock(256, 512)

        # -------------------------
        # Pooling
        # -------------------------

        self.pool = nn.MaxPool2d(
            kernel_size=2,
            stride=2
        )

        # -------------------------
        # Bottleneck
        # 512 + 512 = 1024
        # -------------------------

        self.bottleneck = ConvBlock(
            1024,
            1024
        )

        # -------------------------
        # Decoder
        # -------------------------

        self.upconv4 = nn.ConvTranspose2d(
            1024,
            512,
            kernel_size=2,
            stride=2
        )

        self.dec_conv4 = ConvBlock(
            1536,
            512
        )

        self.upconv3 = nn.ConvTranspose2d(
            512,
            256,
            kernel_size=2,
            stride=2
        )

        self.dec_conv3 = ConvBlock(
            768,
            256
        )

        self.upconv2 = nn.ConvTranspose2d(
            256,
            128,
            kernel_size=2,
            stride=2
        )

        self.dec_conv2 = ConvBlock(
            384,
            128
        )

        self.upconv1 = nn.ConvTranspose2d(
            128,
            64,
            kernel_size=2,
            stride=2
        )

        self.dec_conv1 = ConvBlock(
            192,
            64
        )

        # -------------------------
        # Output
        # -------------------------

        self.final_conv = nn.Conv2d(
            64,
            1,
            kernel_size=1
        )

    def forward(self, image1, image2):

        # =====================================
        # Encoder 1
        # =====================================

        e1_1 = self.enc1_conv1(image1)
        p1_1 = self.pool(e1_1)

        e1_2 = self.enc1_conv2(p1_1)
        p1_2 = self.pool(e1_2)

        e1_3 = self.enc1_conv3(p1_2)
        p1_3 = self.pool(e1_3)

        e1_4 = self.enc1_conv4(p1_3)
        p1_4 = self.pool(e1_4)

        # =====================================
        # Encoder 2
        # =====================================

        e2_1 = self.enc2_conv1(image2)
        p2_1 = self.pool(e2_1)

        e2_2 = self.enc2_conv2(p2_1)
        p2_2 = self.pool(e2_2)

        e2_3 = self.enc2_conv3(p2_2)
        p2_3 = self.pool(e2_3)

        e2_4 = self.enc2_conv4(p2_3)
        p2_4 = self.pool(e2_4)

        # =====================================
        # Siamese feature concatenation
        # =====================================

        x = torch.cat(
            [p1_4, p2_4],
            dim=1
        )

        x = self.bottleneck(x)

        # =====================================
        # Decoder
        # =====================================

        x = self.upconv4(x)

        skip4 = torch.cat(
            [e1_4, e2_4],
            dim=1
        )

        x = torch.cat(
            [x, skip4],
            dim=1
        )

        x = self.dec_conv4(x)

        # -------------------------------------

        x = self.upconv3(x)

        skip3 = torch.cat(
            [e1_3, e2_3],
            dim=1
        )

        x = torch.cat(
            [x, skip3],
            dim=1
        )

        x = self.dec_conv3(x)

        # -------------------------------------

        x = self.upconv2(x)

        skip2 = torch.cat(
            [e1_2, e2_2],
            dim=1
        )

        x = torch.cat(
            [x, skip2],
            dim=1
        )

        x = self.dec_conv2(x)

        # -------------------------------------

        x = self.upconv1(x)

        skip1 = torch.cat(
            [e1_1, e2_1],
            dim=1
        )

        x = torch.cat(
            [x, skip1],
            dim=1
        )

        x = self.dec_conv1(x)

        # =====================================
        # Output
        # =====================================

        return self.final_conv(x)