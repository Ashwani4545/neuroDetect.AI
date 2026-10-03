# ml/ — Offline Research & Training Pipeline

This is the **standalone research pipeline** for the core academic problem:
segmentation of the hypodense region from Brain Non-Contrast CT (NCCT) images.
It is separate from `webapp/`, which is the deployed product that *consumes*
a checkpoint this pipeline produces.

```
ml/
├── models/        UNet2p5D architecture (model.py) + an auxiliary classifier
├── training/       train.py, dataset.py, train_classifier.py
├── preprocessing/  preprocess.py — HU windowing / normalization helpers
├── inference/       inference.py — standalone (non-Django) inference CLI
└── evaluation/       visualize.py, report_generator.py
```

## ⚠️ Current status: scaffolding only, not yet trained

Run this before trusting anything below:

```bash
wc -l data/splits/train.csv data/splits/val.csv   # header row only, 0 data rows
```

`configs/config.json` points training at `data/nifti/` + `data/splits/*.csv`,
but **no NCCT volumes, no segmentation masks, and no checkpoint exist in this
repository.** `data/` currently only contains an unrelated MRI tumor-classification
image set (wrong modality, no masks) — not usable for this task.

Because of this, `webapp/core_ml/inference_service.py` never actually loads a
model from here in production; it runs a deterministic HU-windowing/thresholding
fallback instead (see that file's docstring). That fallback is a legitimate,
explainable approach for a portfolio project, but it is **not** the trained
U-Net this pipeline exists to produce, and it should not be described as one.

## To actually train a model

1. Obtain a licensed/ethically-sourced NCCT dataset with paired segmentation
   masks (e.g. via a research data-use agreement — do not use PHI you don't
   have rights to). Convert to NIfTI, place volumes under `data/nifti/`.
2. Populate `data/splits/train.csv` / `val.csv` with `image,mask` rows.
   **Split at the patient/study level**, not the slice level, to avoid
   leakage — `dataset.py` assumes the CSV rows are already correctly split.
3. `python -m ml.training.train` from the repo root (uses `configs/config.json`).
4. Copy the resulting checkpoint into `webapp/checkpoints/` — `webapp/core_ml/model.py`
   will then load it automatically instead of using the heuristic fallback
   (see that file for the exact expected checkpoint filename/shape).
5. Evaluate with real Dice/IoU/Hausdorff metrics before claiming any
   performance number anywhere in the UI or README — see Section 11/39 of the
   project's master development prompt for why this matters.

## Known issue: `ml/models/model.py` vs `webapp/core_ml/model.py`

These two files are still byte-identical, hand-duplicated copies of the same
U-Net architecture. While building the MRI classifier pipeline below, I added
a `sys.path` fix in `webapp/webapp/settings.py` so the Django app can import
directly from `ml/` (that's how the new MRI pipeline avoids a third instance
of this duplication problem). The mechanism now exists to fix this one too —
`webapp/core_ml/model.py` could now just do `from ml.models.model import
UNet2p5D` instead of duplicating the class — but I haven't gone back and made
that specific change, since it means re-verifying the existing CT pipeline
still works identically afterward. Flagging it as the obvious next cleanup
rather than leaving it silently inconsistent.

---

# Brain MRI Disease Classifier (separate pipeline, added for the 3-dataset request)

This is a **second, independent pipeline** — a multi-class MRI classifier,
not related to the NCCT segmentation work above. It exists because MRI and
NCCT are different modalities with different available data; conflating them
would be exactly the mistake Section 3 of the design brief warns against.

## What's real vs not, right now

- ✅ Real, tested code: `ml/training/dataset_mri_classifier.py` (multi-source
  loader), `ml/models/mri_disease_classifier.py` (ResNet18 classifier w/
  Grad-CAM hooks), `ml/training/train_mri_disease_classifier.py` (training
  loop, class-weighted for imbalance), `ml/inference/mri_gradcam_inference.py`
  (classification + Grad-CAM region heatmap). I ran this full pipeline
  end-to-end against synthetic placeholder images (random noise, a handful
  per class) to prove the mechanics work — dataset loading, training loop,
  checkpoint saving, and Grad-CAM inference all execute correctly. That
  proves nothing about real-world accuracy — it's a mechanical smoke test,
  not a trained model. No real MRI data was used or is bundled here.
- ✅ Wired into the Django app (`webapp/core_ml/mri_classifier_analyzer.py`,
  routed from `ingestion.py`) with the same honest pattern as the CT pipeline:
  if no checkpoint is installed, it says so plainly instead of faking a result.
- ❌ Not trained. I could not actually download any of the three datasets
  you provided — `kaggle.com` and `drive.google.com` are not reachable from
  this development sandbox (only package registries like pypi.org are
  allowlisted), and Google Drive folder listings require a signed-in browser
  session even if they were reachable. So there is no checkpoint, and no
  accuracy number is claimed anywhere.

## What "which region is affected" actually means here

None of the three datasets you provided have pixel-level segmentation masks
— they're whole-image classification labels only (this MRI scan = glioma /
meningioma / pituitary tumor / normal / atrophy / WMI / ischemia). There's no
ground truth to train a true segmentation model from.

The honest way to give an approximate "affected region" from a
classification-only dataset is **Grad-CAM**: a heatmap of which pixels most
influenced the model's decision. `mri_gradcam_inference.py` implements this
and reports a coarse **image-quadrant** description ("upper-left region of
the scan") — deliberately not a real anatomical label like "left temporal
lobe," because that would need registration to a brain atlas, which this
model doesn't and can't do. Keep that distinction intact anywhere this output
is shown.

## Combining your three datasets — what I know and don't

| Dataset | Classes | Size | Status |
|---|---|---|---|
| `masoudnickparvar/brain-tumor-mri-dataset` (Kaggle) | glioma, meningioma, pituitary, no tumor | ~7,023 images | Known structure (standard Kaggle `Training/<class>/`, `Testing/<class>/` layout) — mapped in `CLASS_FOLDER_MAP` |
| `turkertuncer/brain-disorders-four-categories` (Kaggle) | normal, brain atrophy, white matter intensity (WMI), ischemia | 444 images total (100/150/92/102 per the paper this dataset accompanies) | Structure **inferred from the dataset's academic paper**, not verified against the actual downloaded files — I could not download it to check real folder names. **You'll need to verify/fix `CLASS_FOLDER_MAP` in `dataset_mri_classifier.py` once you've actually extracted it.** |
| Your Google Drive folder ("Brain Disease Dataset") | Unknown | Unknown | I could only see the folder's title, not its contents — Drive requires a signed-in session to list files, which this sandbox doesn't have. **Tell me the folder/class structure once you've looked, and I'll wire it into `CLASS_FOLDER_MAP` properly instead of guessing.** |

Two real caveats to know about before you train on the combined set:

1. **Severe class imbalance**: ~7,000 tumor images vs. 444 total for the
   other 4 classes. `train_mri_disease_classifier.py` uses inverse-frequency
   class weighting, which helps but doesn't fully fix a >10x gap — expect
   atrophy/WMI/ischemia to be the weakest-performing classes until you have
   more data for them.
2. **Cross-dataset domain shift**: `masoudnickparvar`'s "notumor" and
   `turkertuncer`'s "normal" images come from different sources/scanners.
   Merging them into one "no_tumor" class risks the model partly learning to
   recognize *which dataset an image came from* rather than pure pathology.
   After training, check a confusion matrix broken down by source dataset,
   not just by class, before trusting the "no_tumor" class's real-world
   accuracy.

## How to actually train this

1. On a machine with real internet access (your laptop, Colab, or a Kaggle
   notebook — Colab's free GPU tier is enough for a dataset this size):
   ```bash
   pip install kaggle
   kaggle datasets download -d masoudnickparvar/brain-tumor-mri-dataset -p data/mri_raw/brain_tumor_mri --unzip
   kaggle datasets download -d turkertuncer/brain-disorders-four-categories -p data/mri_raw/brain_disorders_four_categories --unzip
   ```
   (requires a free Kaggle API token — kaggle.com → Account → Create New API Token)
2. Download your Google Drive folder manually and place it under
   `data/mri_raw/<a folder name you choose>/`, then add its class folder
   names to `CLASS_FOLDER_MAP` in `ml/training/dataset_mri_classifier.py`.
3. `ls` into the extracted folders and confirm the class subfolder names
   actually match `CLASS_FOLDER_MAP` — fix any mismatches (I couldn't verify
   `turkertuncer`'s real folder names, see table above).
4. Add the new dataset's path to `dataset_roots` in `configs/mri_classifier_config.json`.
5. Train:
   ```bash
   python -m ml.training.train_mri_disease_classifier --config configs/mri_classifier_config.json
   ```
6. Copy the result: `checkpoints_mri_classifier/best_mri_classifier.pth` →
   `webapp/checkpoints_mri_classifier/best_mri_classifier.pth`. The Django
   app will then automatically start using it instead of the "not trained
   yet" fallback message — no code changes needed.
7. Look at `checkpoints_mri_classifier/best_metrics.json` (per-class F1, not
   just accuracy — accuracy is misleading on an imbalanced dataset like this)
   before deciding it's good enough to show anyone.

