import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import CORS_ORIGINS
from app.database import init_db
from app.api import routes_health, routes_model, routes_analysis

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('neurodetect-backend')


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info('Database initialized.')
    yield


app = FastAPI(
    title='NeuroDetect AI API',
    description='Brain NCCT hypodense-region segmentation — research/decision-support API. Not a diagnostic device.',
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f'Unhandled error on {request.method} {request.url.path}')
    return JSONResponse(status_code=500, content={'detail': 'An internal error occurred. Please try again.'})


app.include_router(routes_health.router, prefix='/api', tags=['health'])
app.include_router(routes_model.router, prefix='/api', tags=['model'])
app.include_router(routes_analysis.router, prefix='/api', tags=['analysis'])
