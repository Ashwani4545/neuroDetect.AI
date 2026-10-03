from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import HealthStatus

router = APIRouter()


@router.get('/health', response_model=HealthStatus)
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text('SELECT 1'))
        db_status = 'connected'
    except Exception as e:
        db_status = f'error: {e}'
    return HealthStatus(status='ok', database=db_status)
