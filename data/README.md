# data/

- `ST000001/` — a real sample brain CT DICOM study (kept). This is what the
  Brain CT pipeline was actually developed/tested against.
- `splits/` — training CSV manifests. Currently **empty (header row only)** —
  see `../ml/README.md`.

## Excluded from the downloadable project archive

`Training/`, `testing/`, and `Brain_MRI_conditions.csv` were removed before
packaging — they're a ~200MB Kaggle-style **brain MRI tumor-classification**
image set (wrong modality — MRI, not NCCT; no segmentation masks; not wired
into `ml/training/train.py`'s expected input format). It was taking up the
vast majority of the repo's size for data that isn't usable for this
project's actual segmentation task. If you have the original source and
still want it, it was a standard Brain MRI Tumor dataset off Kaggle — re-download
directly rather than storing it in this repo.
