"""
Thin re-export shim. The actual Brain CT HU-windowing/thresholding pipeline
now lives in ml/inference/ct_pipeline.py — the single shared implementation
used by both this Django app and the FastAPI backend/ (see backend/README.md).
Kept here so existing imports (`from core_ml.inference_service import
get_inference_service`) don't need to change across the Django codebase.
"""
from ml.inference.ct_pipeline import get_inference_service, InferenceService  # noqa: F401
