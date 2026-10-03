import io
import json
import os

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.config import UPLOAD_DIR, RESULTS_DIR
from app.database import get_db
from app.models_db import Analysis
from app.schemas import AnalysisDetail, AnalysisHistoryResponse
from app.services.analysis_service import ValidationError, validate_upload, save_upload, run_analysis

router = APIRouter()


def _to_detail(a: Analysis) -> AnalysisDetail:
    return AnalysisDetail(
        id=a.id, created_at=a.created_at, original_filename=a.original_filename,
        status=a.status, detected=a.detected, confidence=a.confidence,
        model_used=a.model_used, error_message=a.error_message,
        processing_time_ms=a.processing_time_ms, measurements=a.measurements,
        mask_available=bool(a.mask_filename), overlay_available=bool(a.overlay_filename),
    )


def _get_or_404(db: Session, analysis_id: str) -> Analysis:
    a = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if a is None:
        raise HTTPException(status_code=404, detail='Analysis not found.')
    return a


@router.post('/analysis/upload', response_model=AnalysisDetail)
async def upload_analysis(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    try:
        validate_upload(file, contents)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    stored_name = save_upload(file, contents)
    analysis = Analysis(original_filename=file.filename, stored_filename=stored_name, status='pending')
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    return _to_detail(analysis)


@router.post('/analysis/predict/{analysis_id}', response_model=AnalysisDetail)
def predict_analysis(analysis_id: str, db: Session = Depends(get_db)):
    analysis = _get_or_404(db, analysis_id)
    if analysis.status == 'processing':
        raise HTTPException(status_code=409, detail='Analysis is already processing.')
    analysis = run_analysis(db, analysis)
    return _to_detail(analysis)


@router.get('/analysis/history', response_model=AnalysisHistoryResponse)
def analysis_history(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: str | None = Query(None, alias='status'),
    search: str | None = Query(None),
    sort: str = Query('created_at_desc', pattern='^(created_at_desc|created_at_asc)$'),
):
    q = db.query(Analysis)
    if status_filter:
        q = q.filter(Analysis.status == status_filter)
    if search:
        q = q.filter(Analysis.original_filename.ilike(f'%{search}%'))
    q = q.order_by(Analysis.created_at.desc() if sort == 'created_at_desc' else Analysis.created_at.asc())

    total = q.count()
    results = q.offset((page - 1) * page_size).limit(page_size).all()
    return AnalysisHistoryResponse(total=total, page=page, page_size=page_size, results=[_to_detail(a) for a in results])


@router.get('/analysis/{analysis_id}', response_model=AnalysisDetail)
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    return _to_detail(_get_or_404(db, analysis_id))


@router.delete('/analysis/{analysis_id}')
def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    analysis = _get_or_404(db, analysis_id)
    for fname, folder in [
        (analysis.stored_filename, UPLOAD_DIR),
        (analysis.mask_filename, RESULTS_DIR),
        (analysis.overlay_filename, RESULTS_DIR),
    ]:
        if fname:
            path = os.path.join(folder, fname)
            if os.path.exists(path):
                os.remove(path)
    db.delete(analysis)
    db.commit()
    return {'success': True, 'id': analysis_id}


@router.get('/analysis/{analysis_id}/original')
def get_original(analysis_id: str, db: Session = Depends(get_db)):
    analysis = _get_or_404(db, analysis_id)
    path = os.path.join(UPLOAD_DIR, analysis.stored_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='Original file missing on disk.')
    ext = os.path.splitext(path)[1].lower()
    media_type = 'application/dicom' if ext == '.dcm' else f'image/{"jpeg" if ext in (".jpg", ".jpeg") else "png"}'
    return FileResponse(path, media_type=media_type)


@router.get('/analysis/{analysis_id}/mask')
def get_mask(analysis_id: str, db: Session = Depends(get_db)):
    analysis = _get_or_404(db, analysis_id)
    if not analysis.mask_filename:
        raise HTTPException(status_code=404, detail='No mask available for this analysis.')
    path = os.path.join(RESULTS_DIR, analysis.mask_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='Mask file missing on disk.')
    return FileResponse(path, media_type='image/png')


@router.get('/analysis/{analysis_id}/overlay')
def get_overlay(analysis_id: str, db: Session = Depends(get_db)):
    analysis = _get_or_404(db, analysis_id)
    if not analysis.overlay_filename:
        raise HTTPException(status_code=404, detail='No overlay available for this analysis.')
    path = os.path.join(RESULTS_DIR, analysis.overlay_filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail='Overlay file missing on disk.')
    return FileResponse(path, media_type='image/png')


@router.get('/analysis/{analysis_id}/export')
def export_analysis(analysis_id: str, format: str = Query('json', pattern='^(json|pdf)$'), db: Session = Depends(get_db)):
    analysis = _get_or_404(db, analysis_id)
    detail = _to_detail(analysis)

    disclaimer = (
        "AI-generated segmentation — requires expert review. This output is a "
        "research/decision-support artifact, not a clinical diagnosis, and does "
        "not determine treatment. It has not been reviewed by a radiologist."
    )

    if format == 'json':
        payload = {**json.loads(detail.model_dump_json()), 'disclaimer': disclaimer}
        buf = io.BytesIO(json.dumps(payload, indent=2).encode('utf-8'))
        return StreamingResponse(
            buf, media_type='application/json',
            headers={'Content-Disposition': f'attachment; filename="analysis_{analysis_id}.json"'},
        )

    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas as pdf_canvas
    except ImportError:
        raise HTTPException(
            status_code=501,
            detail="PDF export requires the 'reportlab' package, which isn't installed in this "
                   "environment. Use format=json, or `pip install reportlab` and restart the backend.",
        )

    buf = io.BytesIO()
    c = pdf_canvas.Canvas(buf, pagesize=letter)
    width, height = letter
    y = height - 50
    c.setFont('Helvetica-Bold', 14)
    c.drawString(50, y, 'NeuroDetect AI — Analysis Report')
    y -= 25
    c.setFont('Helvetica', 9)
    c.drawString(50, y, '(Research / decision-support output — not a clinical diagnosis)')
    y -= 30

    c.setFont('Helvetica', 10)
    lines = [
        f"Analysis ID: {analysis.id}",
        f"Created: {analysis.created_at}",
        f"Original filename: {analysis.original_filename}",
        f"Status: {analysis.status}",
        f"Model used: {analysis.model_used or 'N/A'}",
        f"Confidence: {analysis.confidence or 'N/A'}",
        f"Detected: {analysis.detected}",
        f"Processing time: {analysis.processing_time_ms} ms" if analysis.processing_time_ms else "Processing time: N/A",
    ]
    for line in lines:
        c.drawString(50, y, line)
        y -= 16

    y -= 10
    c.setFont('Helvetica-Bold', 10)
    c.drawString(50, y, 'Quantitative Measurements:')
    y -= 16
    c.setFont('Helvetica', 9)
    m = analysis.measurements or {}
    if m.get('available'):
        for line in [
            f"Foreground pixels: {m.get('total_foreground_pixels')}",
            f"Foreground percentage: {m.get('foreground_percentage')}%",
            f"Region count: {m.get('region_count')}",
            f"Units: pixels only ({m.get('physical_units_note', '')[:90]}...)",
        ]:
            c.drawString(60, y, line)
            y -= 14
    else:
        c.drawString(60, y, 'Not available.')
        y -= 14

    y -= 20
    c.setFont('Helvetica-Oblique', 8)
    text_obj = c.beginText(50, y)
    text_obj.textLines(disclaimer)
    c.drawText(text_obj)

    c.showPage()
    c.save()
    buf.seek(0)
    return StreamingResponse(
        buf, media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="analysis_{analysis_id}.pdf"'},
    )
