# NeuroDetect AI — React Frontend

Vite + React + TypeScript + Tailwind. Pairs with `../backend/` (FastAPI) —
see `../backend/README.md` for how this fits alongside the separate Django
implementation in `../webapp/`.

## Pages
- **Landing** (`/`) — overview, disclaimer, entry point
- **Upload** (`/upload`) — drag-and-drop, client-side validation, preview, kicks off upload + predict
- **Analysis** (`/analysis/:id`) — the workspace + results page combined: a Canvas-based viewer
  (original / mask / overlay / side-by-side, adjustable overlay opacity, zoom via scroll, pan via drag),
  quantitative measurements table, region list, JSON/PDF export
- **History** (`/history`) — search, status filter, pagination, delete with confirmation
- **Model Info** (`/model`) — live checkpoint status from the backend, no fabricated metrics
- **Settings** (`/settings`) — theme, default overlay opacity (both persisted to `localStorage`), backend health

## Running locally

```bash
npm install
cp .env.example .env   # point VITE_API_BASE_URL at your backend if not localhost:8000
npm run dev             # http://localhost:5173, proxies /api to the backend in dev
```

## Build

```bash
npm run build    # runs `tsc -b` then `vite build` — type-checked, verified to build clean
```

## Known gaps

- No auth (matches the backend — see its README).
- The Canvas viewer tints the mask red client-side for the adjustable-opacity
  overlay; it doesn't yet support DICOM windowing controls in-browser (DICOM
  windowing happens server-side in `ml/inference/ct_pipeline.py` before the
  mask/overlay PNGs are generated).
