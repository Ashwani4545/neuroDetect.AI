
# 🧠 NeuroDetect AI — Multi-Modality Medical Intelligence Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![Django](https://img.shields.io/badge/Django-6.0-green?style=for-the-badge&logo=django)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-red?style=for-the-badge&logo=pytorch)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-lightblue?style=for-the-badge&logo=opencv)
![License](https://img.shields.io/badge/License-Academic-yellow?style=for-the-badge)

**An AI-assisted research/decision-support platform that analyzes brain CT, chest X-rays, ECG traces, blood-test PDFs, skin photos, retinal photos, and bone X-rays — with a Django auth system, risk profiling, a rule-based chatbot, and a simulated telehealth flow.**

</div>

> **Naming note:** this project is now consistently branded **NeuroDetect AI** across the live UI, chatbot, and docs. It briefly ran under an internal working name, `MediAssist.AI`, while the platform expanded past brain-CT-only — that name is no longer used anywhere in the UI. A couple of deployment artifacts (the Hugging Face Space slug `mediassist-ai`, and the matching entry in `CSRF_TRUSTED_ORIGINS` in `settings.py`) still reference the old name because they're tied to real, already-provisioned infrastructure — renaming those requires actually renaming the HF Space itself, not just a text edit, so they're flagged rather than silently changed.

---

## 🎯 What it actually does today

1. **Detects the report modality** — routes CT scans, chest X-rays, ECG traces, blood-test PDFs, skin photos, retinal photos, and bone X-rays to the right analyzer. See [Modality detection: how it actually works](#-modality-detection-how-it-actually-works) below — it's mostly filename/aspect-ratio based, not content classification, and it now says so honestly when it's guessing.
2. **Runs a deterministic, explainable analysis** on the primary Brain CT pipeline (HU-windowing + thresholding — see below). The other modalities run comparable classical-CV/heuristic checks in `webapp/core_ml/`.
3. **Generates plain-English explanations**, condition context, dietary/herbal guidance, and doctor-discussion questions (`disease_knowledge.py`, `guidance.py`).
4. **Calculates approximate 10-year cardiovascular/diabetes/stroke risk profiles** from entered vitals.
5. **Offers a rule-based, fully offline chatbot** grounded in the scan's own findings (`mediassist_chatbot.py` + a small local RAG corpus — no external LLM calls today).
6. **Simulates a telehealth "doctor room"** — request a consult, get sample specialist matches, chat, sign off. This directory is illustrative sample data, clearly labeled as such in the UI — not real, verified doctors.
7. **Full Django auth + per-user scan history**, with ownership-scoped API access (see [Security](#-security-status) below).

---

## ⚠️ Current status — read this before assuming anything is "done"

Being explicit about this is more valuable than a longer feature list. Per this project's own stated principle: *UI implemented ≠ model trained ≠ clinically validated.*

| Claim | Status |
|---|---|
| Brain CT/NCCT hypodense-region "detection" works | ✅ Yes — via a **deterministic physics-based pipeline** (HU windowing + adaptive thresholding), not a trained model. See below. |
| A trained U-Net segmentation model exists | ❌ **No.** `ml/training/train.py` and the architecture in `ml/models/model.py` are real and correctly built for this task, but **no NCCT+mask dataset has ever been loaded** — `data/splits/train.csv`/`val.csv` are empty (header row only), `data/nifti/` doesn't exist, and no `.pth` checkpoint exists anywhere. See `ml/README.md` for the full story and what's needed to actually train it. |
| Any performance/accuracy metric (Dice, IoU, etc.) | ❌ Not applicable — nothing has been evaluated, because nothing has been trained. No number is quoted anywhere in this repo for exactly that reason. |
| Chest X-ray / ECG / blood / skin / retinal / bone analyzers | ⚠️ Classical CV/rule-based heuristics (`core_ml/*.py`), not trained models either. Useful as an explainable baseline, not clinically validated. |
| Brain MRI disease classifier (glioma/meningioma/pituitary/atrophy/WMI/ischemia) | ⚠️ Real, tested pipeline (`ml/models/mri_disease_classifier.py` + Grad-CAM region heatmap) wired into the app — but **not trained**. `kaggle.com` and `drive.google.com` aren't reachable from the dev sandbox this was built in, so no real dataset could be downloaded here. See `ml/README.md` for exact steps to train it yourself. Until then, uploading an MRI returns an explicit "not trained yet" message, not a fabricated result. |
| Auth, per-user data isolation, ownership checks on every API endpoint | ✅ Implemented and covered by an actual test suite (`webapp/segmentation/tests.py`) |
| Modality validation (don't run the CT model on an MRI, etc.) | ✅ Implemented — confidently-identified unsupported modalities (e.g. MRI) are rejected outright; uncertain cases run the fallback pipeline but say so in the UI instead of presenting a guess as confirmed |
| Specialist directory is real, verified doctor data | ❌ No — hardcoded sample data, now explicitly labeled "Demo directory" in the UI |
| Docker / docker-compose local dev | ✅ Production `Dockerfile` (single container, HF-Spaces-ready) + `docker-compose.yml` (adds real Postgres for local dev, plus the FastAPI/React services below) |
| FastAPI + React implementation (`backend/`, `frontend/`) | ✅ Real, tested (7/7 backend tests against the actual sample CT DICOM/JPG; frontend type-checks and builds clean) — but narrower scope than `webapp/` (CT segmentation only, no auth). See `backend/README.md` for exact gaps. |
| MLflow / experiment tracking / model registry | ❌ Not implemented — nothing to track yet without a training run |
| Automated test coverage | ⚠️ Partial — access control and modality-routing logic are tested; the ML analyzers themselves aren't (they need real sample images to test meaningfully) |

---

## 🏗️ Project Structure

> **Two implementations exist side by side.** `webapp/` (Django) is the
> mature, full-featured multi-modality platform documented throughout the
> rest of this README. `backend/` + `frontend/` (FastAPI + React) is a
> second, narrower implementation — brain-CT segmentation only, matching a
> later request to build the platform on that specific stack. Both share the
> same underlying segmentation logic via `ml/inference/ct_pipeline.py`. See
> `backend/README.md` for what that implementation covers and its own
> honest list of gaps (no auth, no background job queue, etc).

```
mediAssist.AI/
│
├── webapp/                        # 🌐 The deployed Django product
│   ├── manage.py
│   ├── core_ml/                   # Analysis engines actually running in production
│   │   ├── model.py                    # 2.5D U-Net architecture (duplicated from ml/models/ — see ml/README.md)
│   │   ├── inference_service.py        # Brain CT: dual-mode HU-thresholding pipeline
│   │   ├── ingestion.py                # Modality router — confirmed vs inferred vs fallback
│   │   ├── chest_xray.py / ecg.py / blood_test.py / skin_analyzer.py / retinal_analyzer.py / bone_xray_analyzer.py
│   │   ├── disease_knowledge.py / guidance.py    # Condition explanations + diet/lifestyle guidance
│   │   ├── risk_profiler.py            # 10-year CV/diabetes/stroke risk estimates
│   │   ├── telehealth.py               # Simulated specialist directory + consult flow
│   │   └── rag.py / mediassist_chatbot.py   # Offline, rule-based chatbot
│   ├── segmentation/               # Django app: views, models, urls, templates, tests
│   └── webapp/                     # Django project settings
│
├── ml/                             # Offline research/training pipeline (see ml/README.md)
│   ├── models/      training/      preprocessing/      inference/      evaluation/
│   │       (includes a separate Brain MRI disease classifier + Grad-CAM pipeline — see ml/README.md)
│
├── backend/                        # FastAPI implementation — see backend/README.md
│   └── app/                        # api/, services/, models_db.py, quantitative.py, main.py
├── frontend/                       # React + TS + Vite + Tailwind — see frontend/README.md
│   └── src/                        # pages/, components/ (incl. Canvas-based MedicalImageViewer), services/
│
├── data/                           # See ml/README.md — currently NOT a usable NCCT+mask dataset
├── configs/config.json             # Training hyperparameters
├── docs/legacy/                    # Superseded planning docs & early static prototypes, kept for history
├── docker-compose.yml              # Local dev stack — Django (web/db) + FastAPI/React (backend/frontend)
├── Dockerfile                      # Production image for webapp/ (HF Spaces-ready, port 7860)
├── .env.example
├── requirements.txt
└── README.md
```

---

## ⚙️ Brain CT Pipeline — how the "AI" actually works right now

A **dual-mode, no-training-required, physics-based pipeline**:

### Mode 1 — DICOM (Hounsfield Unit Thresholding)
1. Apply DICOM rescale slope/intercept → true HU values
2. Brain window: **WL = 35, WW = 100** (standard brain CT window)
3. Approximate skull strip via connected-component analysis
4. Hypodense band: **HU 15–35** (below normal parenchyma ~30–45 HU), restricted to the brain mask
5. Morphological open/close + remove regions < 50 px

### Mode 2 — JPG / PNG (Adaptive Intensity Thresholding)
1. CLAHE contrast enhancement
2. Approximate skull stripping
3. Median/MAD-based adaptive threshold (pixels > 1.5×MAD below median flagged)
4. Morphological cleanup + remove regions < 30 px

### Mode 3 — Trained U-Net (not currently active — see status table above)
- 2.5D U-Net, 5-channel pseudo-volume input, automatically used **only if** a `.pth` checkpoint is found at runtime. Today, none exists, so Modes 1–2 are what actually run.

---

## 🔀 Modality detection: how it actually works

`core_ml/ingestion.py` routes files by, in order: PDF → blood-test parser; DICOM `Modality` tag (confirmed); filename keywords (confirmed); image aspect-ratio heuristics (inferred, flagged as such); or — only as a last resort — the Brain CT pipeline (flagged `default_fallback` with an explicit on-screen warning). A filename that says "MRI" now routes to a dedicated MRI disease classifier pipeline (see `ml/README.md`) instead of being run through the CT model — it never gets silently misrouted, and honestly reports "not trained yet" until a real checkpoint is installed. DICOM-format MRI specifically is still rejected outright (not yet wired up — see `ml/README.md`).

---

## 🔒 Security status

- Every `/api/*` endpoint requires authentication and scopes reads/writes to `request.user` — this was **not** the case in an earlier version of this codebase (endpoints were open and cross-user readable/writable). Fixed and covered by `webapp/segmentation/tests.py`.
- `SECRET_KEY` has no usable hardcoded fallback in a `DEBUG=False` deployment — it fails loudly instead of silently reusing a key that's now public in this repo's history.
- `ALLOWED_HOSTS` has no wildcard by default.
- The simulated telehealth chat still lets the authenticated scan owner tag their own message `is_doctor=true` (no real clinician account model exists yet) — low risk today since it's scoped to their own consult thread, but worth knowing if you ever add real clinician logins.

---

## 🚀 Quick Start — Web Application

### Option A: Docker Compose (recommended — matches production DB)
```bash
git clone https://github.com/Ashwani4545/mediAssist.AI.git
cd mediAssist.AI
cp .env.example .env      # fill in a real SECRET_KEY
docker compose up --build
# → http://localhost:8000
```

### Option B: Local Python
```bash
git clone https://github.com/Ashwani4545/mediAssist.AI.git
cd mediAssist.AI
pip install -r requirements.txt
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

cd webapp
python manage.py migrate
python manage.py test segmentation   # run the test suite
python manage.py runserver
# → http://127.0.0.1:8000/
```

Register an account, then upload a brain CT (JPG, PNG, or `.dcm`), a chest X-ray, ECG image, blood-test PDF, skin/retinal photo, or bone X-ray.

---

## 🧪 Training the segmentation model (not yet possible — see status table)

The pipeline is real and ready; the data isn't. If you have (or obtain, with proper rights/ethics approval) a real NCCT + segmentation-mask dataset:

```bash
# 1. Populate data/splits/train.csv and val.csv with image,mask rows
#    (split at patient/study level — see ml/README.md)
# 2. Preprocess DICOM → NIfTI
python -m ml.preprocessing.preprocess --input_dir data/raw --output_dir data/nifti --spacing 1.0 1.0 5.0
# 3. Train
python -m ml.training.train --config configs/config.json
# 4. Copy the resulting checkpoint into webapp/checkpoints/ so inference_service.py picks it up
```

Full details, including the dataset-leakage caveat and the model.py duplication issue: [`ml/README.md`](ml/README.md).

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Web Framework** | Django 6.0 |
| **ML / DL** | PyTorch 2.x, 2.5D U-Net (built, not yet trained) |
| **Image Processing** | OpenCV, NumPy, scikit-image |
| **Medical Imaging** | pydicom, nibabel, SimpleITK |
| **Database** | PostgreSQL (via `dj-database-url`), sqlite fallback for quick local runs |
| **Frontend** | Vanilla HTML/CSS/JS |
| **Language** | Python 3.11+ |

---

## ⚠️ Disclaimer

> This software is intended for **academic and research purposes only**. It is **not a certified medical device** and must not be used for clinical diagnosis without review by a qualified medical professional. If you or someone else has sudden weakness, facial drooping, slurred speech, a sudden severe headache, loss of consciousness, seizures, or other potentially life-threatening symptoms, **do not wait for this tool** — contact local emergency services immediately. This repository does not contain real patient medical images. The specialist directory is illustrative sample data, not verified real-world doctors.

---

## 👨‍💻 Author

```
Ashwani Pandey
Project : NeuroDetect AI (brain NCCT hypodense-region focus, expanded to multi-modality)
Stack   : Django · PyTorch · OpenCV · pydicom
Use     : Academic & Research Purposes Only
```

## 📸 Application Preview

<img width="1498" height="635" alt="image" src="https://github.com/user-attachments/assets/eaed19fc-2131-4338-9b76-573c3e6a94e3" />
<img width="1517" height="637" alt="image" src="https://github.com/user-attachments/assets/9d94f530-da8f-4787-9235-35ab955c193c" />
<img width="1501" height="527" alt="image" src="https://github.com/user-attachments/assets/fcca9c25-47fb-4df1-bc77-ee8ad4645933" />
<img width="1505" height="528" alt="image" src="https://github.com/user-attachments/assets/34b2b8d6-d79f-4a0c-9bc1-658d61ed9c60" />
<img width="1507" height="522" alt="image" src="https://github.com/user-attachments/assets/d79feeda-84bc-4b69-bd0a-facfc1f42d26" />
<img width="1502" height="435" alt="image" src="https://github.com/user-attachments/assets/2f5d72e8-ea49-483f-a1ac-f1a8beb82d57" />
<img width="1483" height="372" alt="image" src="https://github.com/user-attachments/assets/b6193533-598d-4cc0-872a-90cdfdc53c9b" />
<img width="1482" height="403" alt="image" src="https://github.com/user-attachments/assets/84fae1be-bd1d-4539-8779-012b0a48af62" />
<img width="1505" height="625" alt="image" src="https://github.com/user-attachments/assets/1484d721-9bc1-4613-a5b3-e018a7d04273" />
<img width="1507" height="508" alt="image" src="https://github.com/user-attachments/assets/e9eb35e0-a2d1-45c2-8145-8c8543959f1f" />
<img width="1502" height="388" alt="image" src="https://github.com/user-attachments/assets/404195ad-b90b-4d05-950f-c9d6c390de71" />
<img width="1512" height="605" alt="image" src="https://github.com/user-attachments/assets/82355afa-55cd-4a31-8071-ced665e45d6f" />
