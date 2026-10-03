"""
Train the brain MRI disease classifier on the combined, unified dataset.

Usage (once you've actually downloaded and placed the real datasets — see
ml/README.md; this script does nothing useful without them):

    python -m ml.training.train_mri_disease_classifier \
        --config configs/mri_classifier_config.json

What this deliberately does NOT do:
- Does not fabricate or download data itself.
- Does not claim a specific accuracy anywhere — it prints and saves whatever
  the actual run produces, nothing is hardcoded.
- Does not split with random.shuffle across the whole dataset blindly without
  at least warning about the class-imbalance/domain-shift caveats in
  dataset_mri_classifier.py — read those before trusting results.
"""
import argparse
import json
import os

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import transforms

from ml.models.mri_disease_classifier import MRIDiseaseClassifier
from ml.training.dataset_mri_classifier import (
    UNIFIED_CLASSES, discover_samples, MultiSourceMRIDataset,
)


def build_transforms(img_size: int):
    train_tf = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.RandomHorizontalFlip(0.5),
        transforms.RandomRotation(10),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize((img_size, img_size)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    return train_tf, eval_tf


def compute_class_weights(counts: dict) -> torch.Tensor:
    """Inverse-frequency class weights to partially offset the imbalance
    documented in dataset_mri_classifier.py. Partially — not fully — see
    that file's docstring for why a >10x sample gap isn't solved by
    reweighting alone."""
    total = sum(counts.values())
    weights = []
    for cls in UNIFIED_CLASSES:
        n = max(counts.get(cls, 0), 1)
        weights.append(total / (len(UNIFIED_CLASSES) * n))
    return torch.tensor(weights, dtype=torch.float32)


def evaluate(model, loader, device, criterion):
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    all_preds, all_labels = [], []
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            out = model(x)
            loss = criterion(out, y)
            total_loss += loss.item() * x.size(0)
            preds = out.argmax(dim=1)
            correct += (preds == y).sum().item()
            total += x.size(0)
            all_preds.extend(preds.cpu().tolist())
            all_labels.extend(y.cpu().tolist())

    # Macro-F1 by hand (no sklearn dependency assumed) — better than raw
    # accuracy for judging an imbalanced multi-class problem like this one.
    f1s = []
    for c in range(len(UNIFIED_CLASSES)):
        tp = sum(1 for p, l in zip(all_preds, all_labels) if p == c and l == c)
        fp = sum(1 for p, l in zip(all_preds, all_labels) if p == c and l != c)
        fn = sum(1 for p, l in zip(all_preds, all_labels) if p != c and l == c)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f1s.append(f1)
    macro_f1 = float(np.mean(f1s))

    return {
        'loss': total_loss / max(total, 1),
        'accuracy': correct / max(total, 1),
        'macro_f1': macro_f1,
        'per_class_f1': dict(zip(UNIFIED_CLASSES, f1s)),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/mri_classifier_config.json')
    args = parser.parse_args()

    with open(args.config) as f:
        cfg = json.load(f)

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"[train_mri_disease_classifier] device: {device}")

    samples = discover_samples(cfg['dataset_roots'])
    if len(samples) == 0:
        print("[train_mri_disease_classifier] No samples found under the configured "
              "dataset_roots. Nothing to train on — see ml/README.md for how to "
              "download and place the real datasets. Exiting.")
        return

    train_tf, eval_tf = build_transforms(cfg.get('img_size', 224))
    full_ds = MultiSourceMRIDataset(samples, transform=None)  # transform applied per-split below
    counts = full_ds.class_counts()
    print(f"[train_mri_disease_classifier] class counts: {counts}")

    val_frac = cfg.get('val_fraction', 0.15)
    n_val = int(len(full_ds) * val_frac)
    n_train = len(full_ds) - n_val
    train_subset, val_subset = random_split(
        full_ds, [n_train, n_val],
        generator=torch.Generator().manual_seed(cfg.get('seed', 42)),
    )
    # Apply distinct transforms per split via a thin wrapper.
    train_subset.dataset = MultiSourceMRIDataset(samples, transform=train_tf)
    val_subset.dataset = MultiSourceMRIDataset(samples, transform=eval_tf)

    train_loader = DataLoader(train_subset, batch_size=cfg.get('batch_size', 32), shuffle=True, num_workers=cfg.get('num_workers', 2))
    val_loader = DataLoader(val_subset, batch_size=cfg.get('batch_size', 32), shuffle=False, num_workers=cfg.get('num_workers', 2))

    model = MRIDiseaseClassifier(num_classes=len(UNIFIED_CLASSES), pretrained=cfg.get('pretrained', False)).to(device)
    class_weights = compute_class_weights(counts).to(device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.get('lr', 1e-4))

    ckpt_dir = cfg.get('checkpoint_dir', 'checkpoints_mri_classifier')
    os.makedirs(ckpt_dir, exist_ok=True)
    best_f1 = -1.0

    for epoch in range(cfg.get('epochs', 20)):
        model.train()
        running_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * x.size(0)

        metrics = evaluate(model, val_loader, device, criterion)
        print(f"Epoch {epoch}: train_loss={running_loss/max(len(train_subset),1):.4f} "
              f"val_loss={metrics['loss']:.4f} val_acc={metrics['accuracy']:.4f} "
              f"val_macro_f1={metrics['macro_f1']:.4f}")

        if metrics['macro_f1'] > best_f1:
            best_f1 = metrics['macro_f1']
            torch.save({
                'model_state_dict': model.state_dict(),
                'classes': UNIFIED_CLASSES,
                'img_size': cfg.get('img_size', 224),
                'val_metrics': metrics,
            }, os.path.join(ckpt_dir, 'best_mri_classifier.pth'))
            with open(os.path.join(ckpt_dir, 'best_metrics.json'), 'w') as f:
                json.dump(metrics, f, indent=2)
            print(f"  -> new best checkpoint saved (macro_f1={best_f1:.4f})")

    print(f"[train_mri_disease_classifier] Done. Best val macro_f1={best_f1:.4f}. "
          f"Copy {ckpt_dir}/best_mri_classifier.pth into webapp/checkpoints_mri_classifier/ "
          f"for the Django app to pick it up.")


if __name__ == '__main__':
    main()
