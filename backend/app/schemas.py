from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, ConfigDict


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    original_filename: str
    status: str
    detected: Optional[bool] = None
    confidence: Optional[str] = None


class AnalysisDetail(AnalysisSummary):
    model_used: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    measurements: Optional[Any] = None
    mask_available: bool = False
    overlay_available: bool = False


class ModelStatus(BaseModel):
    checkpoint_loaded: bool
    architecture: str
    fallback_pipeline: str
    message: str


class HealthStatus(BaseModel):
    status: str
    database: str


class AnalysisHistoryResponse(BaseModel):
    total: int
    page: int
    page_size: int
    results: list[AnalysisSummary]
