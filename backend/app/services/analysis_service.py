import os
import time
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, RESULTS_DIR, ALLOWED_EXTENSIONS, MAX_UPLOAD_MB
from app.models_db import Analysis
from app.quantitative import compute_measurements


class ValidationError(Exception):
    """Raised for a bad upload — caller maps this to a 400, never a 500."""
    pass


def validate_upload(file: UploadFile, contents: bytes) -> None:
    ext = os.path.splitext(file.filename or '')[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext}'. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_UPLOAD_MB:
        raise ValidationError(f"File too large ({size_mb:.1f} MB). Max allowed: {MAX_UPLOAD_MB} MB.")
    if len(contents) == 0:
        raise ValidationError("Uploaded file is empty.")


def save_upload(file: UploadFile, contents: bytes) -> str:
    ext = os.path.splitext(file.filename or '')[1].lower()
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(stored_path, 'wb') as f:
        f.write(contents)
    return stored_name


def run_analysis(db: Session, analysis: Analysis) -> Analysis:
    """
    Runs the real segmentation pipeline (ml/inference/ct_pipeline.py) against
    the stored file, computes real measurements from the resulting mask, and
    persists the result. Never fabricates a result on failure — marks the
    record 'failed' with the real error message instead.
    """
    analysis.status = 'processing'
    db.commit()

    input_path = os.path.join(UPLOAD_DIR, analysis.stored_filename)
    start = time.time()
    try:
        from ml.inference.ct_pipeline import get_inference_service
        service = get_inference_service()
        result = service.process_image(input_path, RESULTS_DIR)

        elapsed_ms = int((time.time() - start) * 1000)
        mask_path = os.path.join(RESULTS_DIR, result['mask_filename'])
        measurements = compute_measurements(mask_path)

        analysis.status = 'completed'
        analysis.mask_filename = result['mask_filename']
        analysis.overlay_filename = result['overlay_filename']
        analysis.confidence = result['confidence']
        analysis.detected = result['detected']
        analysis.model_used = (
            'Trained 2.5D U-Net checkpoint'
            if getattr(service, 'model', None) is not None
            else 'HU-windowing / adaptive-thresholding pipeline (no trained checkpoint installed)'
        )
        analysis.processing_time_ms = elapsed_ms
        analysis.measurements = measurements
        analysis.error_message = None

    except Exception as e:
        analysis.status = 'failed'
        analysis.error_message = str(e)

    db.commit()
    db.refresh(analysis)
    return analysis
