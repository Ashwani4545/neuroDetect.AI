import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, JSON, Integer

from app.database import Base


def _new_id() -> str:
    return uuid.uuid4().hex


class Analysis(Base):
    """
    One record per uploaded-image analysis. Large image artifacts (original,
    mask, overlay) are stored as files on disk under UPLOAD_DIR/RESULTS_DIR —
    only their filenames are stored here, per the spec's requirement not to
    put raw image bytes in ordinary DB columns.
    """
    __tablename__ = 'analyses'

    id = Column(String, primary_key=True, default=_new_id)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)   # on disk under UPLOAD_DIR
    mask_filename = Column(String, nullable=True)       # on disk under RESULTS_DIR
    overlay_filename = Column(String, nullable=True)    # on disk under RESULTS_DIR

    status = Column(String, default='pending')  # pending | processing | completed | failed
    error_message = Column(String, nullable=True)

    model_used = Column(String, nullable=True)
    confidence = Column(String, nullable=True)
    detected = Column(Boolean, nullable=True)

    processing_time_ms = Column(Integer, nullable=True)
    measurements = Column(JSON, nullable=True)
