# NeuroDetect AI — FastAPI Backend

A second, parallel implementation of the brain-NCCT hypodense-region
segmentation platform, built on the stack requested in the project's
FastAPI/React specification: **FastAPI + SQLAlchemy + a real Canvas-based
React viewer**, instead of the original Django + vanilla-JS implementation
in `webapp/`.

**This does not replace `webapp/`.** Both exist side by side:
- `webapp/` — the mature, full-featured Django app (multi-modality: CT, chest
  X-ray, ECG, blood tests, skin/retinal/bone X-ray, MRI classifier, auth,
  telehealth, chatbot, risk profiling). Production-tested, larger scope.
- `backend/` + `frontend/` — this implementation. Narrower scope (brain NCCT
  segmentation only, matching the spec's stated primary objective), no auth,
  no multi-modality support — but a cleaner separation of concerns and the
  specific tech stack (FastAPI, TypeScript, Canvas viewer) the spec asked for.

Both share the exact same underlying segmentation logic —
`ml/inference/ct_pipeline.py` is the single source of truth, imported by
both `webapp/core_ml/inference_service.py` (a thin re-export shim) and this
backend directly.

## What's real vs. not

- ✅ **Real, tested**: every endpoint below actually runs, against the real
  `ml/inference/ct_pipeline.py` pipeline (HU-windowing/adaptive-thresholding
  — the same deterministic, explainable method used in `webapp/`, since no
  trained U-Net checkpoint exists — see `ml/README.md`). `tests/test_api.py`
  exercises the complete upload → predict → view → export → delete flow
  against `data/ST000001/`, a genuine sample brain CT bundled in this repo —
  not synthetic/mocked data. All 7 tests pass.
- ❌ **Not implemented**: authentication (this backend has none — anyone who
  can reach it can see/delete any analysis; fine for a local research
  prototype, not for a multi-user deployment without adding it first),
  background job queue (predict is synchronous — fine for single images,
  would need a task queue like Celery/RQ for real concurrency at scale),
  scheduled data-retention purging (the `DATA_RETENTION_DAYS` config exists
  but nothing currently acts on it — deletion is manual, via the History
  page or `DELETE /api/analysis/{id}`).

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness + DB connectivity |
| GET | `/api/model/status` | Honest checkpoint status — never fabricates "trained" |
| POST | `/api/analysis/upload` | Validate + store a file, returns a `pending` analysis |
| POST | `/api/analysis/predict/{id}` | Run the real pipeline on a stored upload |
| GET | `/api/analysis/{id}` | Full analysis detail |
| GET | `/api/analysis/history` | Paginated, searchable, filterable list |
| DELETE | `/api/analysis/{id}` | Deletes the record + its files on disk |
| GET | `/api/analysis/{id}/original` | Serves the original uploaded file |
| GET | `/api/analysis/{id}/mask` | Serves the raw binary segmentation mask PNG |
| GET | `/api/analysis/{id}/overlay` | Serves a pre-composited overlay PNG |
| GET | `/api/analysis/{id}/export?format=json\|pdf` | Structured report export |

Interactive docs at `/docs` (Swagger UI) once running.

## Running locally

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # defaults work as-is for local dev
PYTHONPATH=..:. uvicorn app.main:app --reload --port 8000
```

`PYTHONPATH` must include the repo root so `ml/` is importable — the
Dockerfile handles this automatically (see below); it's the one thing to
remember when running outside Docker.

## Running the tests

```bash
cd backend
PYTHONPATH=..:. pytest tests/ -v
```

## Docker

```bash
docker compose up --build backend frontend
```
(from the repo root — see the root `docker-compose.yml`. Runs alongside the
existing Django `web`/`db` services without port conflicts: backend on
`:8001`, frontend on `:5174`.)

## Known gaps if you extend this

- No auth — add it before exposing this beyond localhost.
- `predict` is synchronous — fine for single-image research use; move to a
  background task queue if you need to handle concurrent large uploads.
- DICOM-format originals aren't rendered client-side (browsers can't display
  raw DICOM) — the frontend correctly skips the "original" view for `.dcm`
  uploads and shows the mask/overlay instead, which are rendered server-side
  from the DICOM pixel data. A proper fix would render a PNG preview
  server-side at upload time.
