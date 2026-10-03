"""
Loads a trained MRIDiseaseClassifier checkpoint and runs inference, producing:
  1. a predicted class + confidence
  2. a Grad-CAM heatmap showing which pixels most influenced that prediction

On "region affected": Grad-CAM tells you where in the *image* the model
looked, not a calibrated neuroanatomical coordinate (that would require
registering the scan to a brain atlas, which is out of scope here and isn't
something a plain classifier can do). This module deliberately reports a
coarse image-quadrant description ("upper-left region of the scan") rather
than an anatomical label like "temporal lobe" — the latter would overclaim
precision the model doesn't have. Keep that framing wherever this output
reaches the UI.
"""
import os
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image
from torchvision import transforms

from ml.models.mri_disease_classifier import MRIDiseaseClassifier

NORMALIZE = transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])


def _quadrant_description(heatmap: np.ndarray) -> str:
    """Coarse, honestly-scoped location description from a Grad-CAM heatmap's
    center of mass — image-space quadrant only, not an anatomical label."""
    h, w = heatmap.shape
    ys, xs = np.mgrid[0:h, 0:w]
    total = heatmap.sum()
    if total <= 0:
        return "no clearly localized region (diffuse or low-signal activation)"
    cy = (ys * heatmap).sum() / total
    cx = (xs * heatmap).sum() / total
    vert = "upper" if cy < h / 2 else "lower"
    horiz = "left" if cx < w / 2 else "right"
    if abs(cy - h / 2) < h * 0.15 and abs(cx - w / 2) < w * 0.15:
        return "central region of the scan"
    return f"{vert}-{horiz} region of the scan"


class MRIGradCAMInference:
    def __init__(self, checkpoint_path: str, device: str = None):
        self.device = torch.device(device or ('cuda' if torch.cuda.is_available() else 'cpu'))
        ckpt = torch.load(checkpoint_path, map_location=self.device)
        self.classes = ckpt['classes']
        self.img_size = ckpt.get('img_size', 224)
        self.model = MRIDiseaseClassifier(num_classes=len(self.classes), pretrained=False)
        self.model.load_state_dict(ckpt['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()

    def _preprocess(self, image_path: str) -> torch.Tensor:
        img = Image.open(image_path).convert('RGB').resize((self.img_size, self.img_size))
        tensor = transforms.ToTensor()(img)
        tensor = NORMALIZE(tensor)
        return tensor.unsqueeze(0).to(self.device)

    def predict(self, image_path: str, output_dir: str = None) -> dict:
        x = self._preprocess(image_path)
        x.requires_grad_(False)

        # Forward pass (retains last conv feature map for Grad-CAM)
        logits = self.model(x)
        probs = F.softmax(logits, dim=1)[0]
        pred_idx = int(torch.argmax(probs).item())
        confidence = float(probs[pred_idx].item())

        # Grad-CAM: gradient of the predicted class score w.r.t. the last
        # conv feature map, global-average-pooled into per-channel weights.
        features = self.model.get_last_conv_features()
        features.retain_grad()
        class_score = logits[0, pred_idx]
        self.model.zero_grad()
        class_score.backward(retain_graph=True)

        grads = features.grad[0]                      # (C, H, W)
        weights = grads.mean(dim=(1, 2))               # (C,)
        cam = torch.relu((weights[:, None, None] * features[0]).sum(dim=0))
        cam = cam.detach().cpu().numpy()
        if cam.max() > 0:
            cam = cam / cam.max()

        region_desc = _quadrant_description(cam)

        overlay_path = None
        if output_dir:
            overlay_path = self._save_overlay(image_path, cam, output_dir)

        return {
            'predicted_class': self.classes[pred_idx],
            'confidence': f"{confidence * 100:.1f}%",
            'all_class_probs': {c: f"{float(p) * 100:.1f}%" for c, p in zip(self.classes, probs.tolist())},
            'approximate_region': region_desc,
            'overlay_path': overlay_path,
            'detected': self.classes[pred_idx] != 'no_tumor',
        }

    def _save_overlay(self, image_path: str, cam: np.ndarray, output_dir: str) -> str:
        import cv2
        os.makedirs(output_dir, exist_ok=True)
        orig = cv2.imread(image_path)
        orig = cv2.resize(orig, (self.img_size, self.img_size))
        heatmap = cv2.resize(cam, (self.img_size, self.img_size))
        heatmap = np.uint8(255 * heatmap)
        heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(orig, 0.6, heatmap_color, 0.4, 0)
        out_name = f"gradcam_{os.path.splitext(os.path.basename(image_path))[0]}.png"
        out_path = os.path.join(output_dir, out_name)
        cv2.imwrite(out_path, overlay)
        return out_path
