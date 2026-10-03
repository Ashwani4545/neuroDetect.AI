"""
Loader for the brain-MRI disease classifier, combining multiple
independently-sourced Kaggle-style "one folder per class" datasets into a
single unified label space.

IMPORTANT — honest caveats, read before training on this:

1. Class imbalance across sources: masoudnickparvar's brain-tumor-mri-dataset
   has ~7,000 images across 4 classes; turkertuncer's brain-disorders-four-
   categories has only 444 images across its 4 classes. Naively concatenating
   them means the tumor classes will dominate. `train_mri_disease_classifier.py`
   uses class-weighted loss to compensate, but weighting doesn't fully offset
   a >10x sample-count gap — expect the atrophy/WMI/ischemia classes to be
   the weakest ones until you get more data for them.

2. Domain shift ("no tumor" vs "normal/control"): the two Kaggle sources were
   collected by different groups, likely on different scanners/protocols.
   Treating masoudnickparvar's "notumor" and turkertuncer's "normal" images as
   the same class risks the model learning to distinguish *dataset source*
   (compression artifacts, contrast, framing) rather than actual pathology.
   Inspect a validation confusion matrix broken down by source dataset before
   trusting this class.

3. No segmentation masks anywhere. This dataset only supports whole-image
   classification. "Which region is affected" is produced downstream via
   Grad-CAM (see ml/inference/mri_gradcam_inference.py) — an approximate,
   weakly-supervised heatmap of what the classifier attended to, NOT a
   calibrated anatomical coordinate. Don't present it as more precise than
   that anywhere in the UI.

Expected directory layout (matches Kaggle's default extraction structure):

    data/mri_raw/
        brain_tumor_mri/          # masoudnickparvar/brain-tumor-mri-dataset
            Training/
                glioma/*.jpg
                meningioma/*.jpg
                pituitary/*.jpg
                notumor/*.jpg
            Testing/
                glioma/*.jpg
                ...
        brain_disorders_four_categories/   # turkertuncer/brain-disorders-four-categories
            <whatever folder names Kaggle actually gives you>/*.jpg or *.png

Since I've never been able to actually download and inspect these datasets'
real folder/file layout (no network access to kaggle.com from this
environment), CLASS_FOLDER_MAP below is my best inference from the dataset
descriptions and needs to be checked against what you actually see on disk
after downloading — see ml/README.md for exact instructions and what to fix
if the folder names don't match.
"""
import os
from typing import Dict, List, Tuple

from PIL import Image
from torch.utils.data import Dataset

# Unified label space. Index order matters — this is what the model's output
# layer corresponds to, and must stay in sync with UNIFIED_CLASSES wherever
# a checkpoint trained against it is loaded.
UNIFIED_CLASSES = [
    "no_tumor",     # 0
    "glioma",       # 1
    "meningioma",   # 2
    "pituitary",    # 3
    "atrophy",      # 4
    "wmi",          # 5
    "ischemia",     # 6
]

# Maps: source-dataset subfolder name (lowercased, as Kaggle ships it) -> unified label.
# VERIFY THESE against the real extracted folder names — fix here if they differ.
CLASS_FOLDER_MAP: Dict[str, str] = {
    # masoudnickparvar/brain-tumor-mri-dataset — standard Kaggle folder names
    'notumor': 'no_tumor',
    'no_tumor': 'no_tumor',
    'glioma': 'glioma',
    'meningioma': 'meningioma',
    'pituitary': 'pituitary',

    # turkertuncer/brain-disorders-four-categories — inferred from the dataset's
    # description (100/150/92/102 images: normal, atrophy, WMI, ischemia).
    # The actual on-disk folder names may use different casing/spacing —
    # check `ls data/mri_raw/brain_disorders_four_categories/` after download
    # and add any missing aliases here.
    'normal': 'no_tumor',
    'control': 'no_tumor',
    'atrophy': 'atrophy',
    'brain_atrophy': 'atrophy',
    'wmi': 'wmi',
    'white_matter_intensity': 'wmi',
    'white matter intensity': 'wmi',
    'ischemia': 'ischemia',
    'ischemic': 'ischemia',
}

IMG_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.bmp')


def discover_samples(dataset_roots: List[str]) -> List[Tuple[str, int]]:
    """
    Walk one or more dataset root directories (each containing class
    subfolders at any depth — handles Kaggle's Training/<class>/ and
    Testing/<class>/ split folders transparently) and return a flat list of
    (filepath, unified_label_index) pairs.

    Silently skips folders that don't match any entry in CLASS_FOLDER_MAP —
    prints a warning listing unmatched folder names so you can fix the map
    rather than silently lose data.
    """
    samples = []
    unmatched_folders = set()

    for root in dataset_roots:
        if not os.path.isdir(root):
            print(f"[dataset_mri_classifier] WARNING: root not found, skipping: {root}")
            continue
        for dirpath, _, filenames in os.walk(root):
            folder_name = os.path.basename(dirpath).strip().lower()
            if folder_name not in CLASS_FOLDER_MAP:
                if any(f.lower().endswith(IMG_EXTENSIONS) for f in filenames):
                    unmatched_folders.add(os.path.basename(dirpath))
                continue
            unified_label = CLASS_FOLDER_MAP[folder_name]
            label_idx = UNIFIED_CLASSES.index(unified_label)
            for fname in filenames:
                if fname.lower().endswith(IMG_EXTENSIONS):
                    samples.append((os.path.join(dirpath, fname), label_idx))

    if unmatched_folders:
        print(f"[dataset_mri_classifier] WARNING: found image folders with no "
              f"class mapping (skipped, add them to CLASS_FOLDER_MAP if they're "
              f"real classes): {sorted(unmatched_folders)}")

    return samples


class MultiSourceMRIDataset(Dataset):
    def __init__(self, samples: List[Tuple[str, int]], transform=None):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img, label

    def class_counts(self) -> Dict[str, int]:
        counts = {c: 0 for c in UNIFIED_CLASSES}
        for _, label in self.samples:
            counts[UNIFIED_CLASSES[label]] += 1
        return counts
