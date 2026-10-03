import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/

DATABASE_URL = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'app.db')}")

UPLOAD_DIR = os.environ.get('UPLOAD_DIR', os.path.join(BASE_DIR, 'uploads'))
RESULTS_DIR = os.environ.get('RESULTS_DIR', os.path.join(BASE_DIR, 'results'))
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.dcm'}
MAX_UPLOAD_MB = int(os.environ.get('MAX_UPLOAD_MB', '20'))

CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')

# Retention: how long an analysis + its files are kept before being eligible
# for cleanup. Enforced by DELETE /api/analysis/{id} (user-triggered) today;
# a scheduled auto-purge job is not implemented — see backend/README.md.
DATA_RETENTION_DAYS = int(os.environ.get('DATA_RETENTION_DAYS', '90'))
