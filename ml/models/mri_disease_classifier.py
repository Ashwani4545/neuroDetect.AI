"""
Brain MRI disease classifier. A standard transfer-learning setup
(ResNet18 backbone + a fresh classification head) — not novel architecture,
deliberately: for a dataset this size (thousands, not millions, of images)
a well-understood, hard-to-get-wrong backbone is the right choice over
something exotic.

`pretrained=True` requires downloading ImageNet weights from
download.pytorch.org, which isn't reachable from this development sandbox
(no internet access to that domain) — so it's tested here with
pretrained=False. On a machine with real internet access, use
pretrained=True; transfer learning from ImageNet consistently helps a lot on
datasets this size and there's no reason not to use it when you can.
"""
import torch
import torch.nn as nn
import torchvision.models as models


class MRIDiseaseClassifier(nn.Module):
    def __init__(self, num_classes: int = 7, pretrained: bool = False):
        super().__init__()
        backbone = models.resnet18(
            weights=models.ResNet18_Weights.IMAGENET1K_V1 if pretrained else None
        )
        # Keep everything up to (not including) the final FC layer, so we can
        # both classify AND hook the last conv feature map for Grad-CAM.
        self.stem = nn.Sequential(
            backbone.conv1, backbone.bn1, backbone.relu, backbone.maxpool,
            backbone.layer1, backbone.layer2, backbone.layer3, backbone.layer4,
        )
        self.gap = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(backbone.fc.in_features, num_classes)

        self._last_features = None  # populated on forward(), used by Grad-CAM

    def forward(self, x):
        features = self.stem(x)          # (B, 512, H', W') — the Grad-CAM target layer
        self._last_features = features
        pooled = self.gap(features).flatten(1)
        return self.classifier(pooled)

    def get_last_conv_features(self):
        """Feature map from the most recent forward() call, for Grad-CAM."""
        return self._last_features
