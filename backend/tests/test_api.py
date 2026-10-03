"""
Real FastAPI TestClient tests, run against an actual sample DICOM+JPG brain
CT pair from data/ST000001/ — a genuine sample study bundled in the repo.
This is the controlled fixture the spec asks for since no trained model
checkpoint exists to test against; it exercises the real HU-windowing/
thresholding fallback pipeline end-to-end, not a mock.
"""
import io
import os
import sys

import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(BACKEND_DIR)
for p in (BACKEND_DIR, REPO_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ.setdefault('DATABASE_URL', 'sqlite:///:memory:')

from app.main import app  # noqa: E402
from app.database import Base, engine  # noqa: E402

SAMPLE_JPG = os.path.join(REPO_ROOT, 'data', 'ST000001', 'SE000005', 'IM000001.jpg')


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    resp = client.get('/api/health')
    assert resp.status_code == 200
    assert resp.json()['status'] == 'ok'


def test_model_status_honestly_reports_no_checkpoint(client):
    resp = client.get('/api/model/status')
    assert resp.status_code == 200
    data = resp.json()
    assert data['checkpoint_loaded'] is False
    assert 'no trained checkpoint' in data['message'].lower()


def test_upload_rejects_unsupported_extension(client):
    resp = client.post('/api/analysis/upload', files={'file': ('notes.txt', io.BytesIO(b'hello'), 'text/plain')})
    assert resp.status_code == 400
    assert 'unsupported file type' in resp.json()['detail'].lower()


def test_upload_rejects_empty_file(client):
    resp = client.post('/api/analysis/upload', files={'file': ('scan.jpg', io.BytesIO(b''), 'image/jpeg')})
    assert resp.status_code == 400


@pytest.mark.skipif(not os.path.exists(SAMPLE_JPG), reason='sample CT image not present')
def test_full_upload_predict_retrieve_flow(client):
    with open(SAMPLE_JPG, 'rb') as f:
        upload_resp = client.post('/api/analysis/upload', files={'file': ('sample_ct.jpg', f, 'image/jpeg')})
    assert upload_resp.status_code == 200
    analysis = upload_resp.json()
    assert analysis['status'] == 'pending'
    analysis_id = analysis['id']

    predict_resp = client.post(f'/api/analysis/predict/{analysis_id}')
    assert predict_resp.status_code == 200
    result = predict_resp.json()
    assert result['status'] == 'completed'
    assert result['mask_available'] is True
    assert result['overlay_available'] is True
    assert result['measurements']['available'] is True
    assert 'no trained checkpoint' in result['model_used'].lower()

    get_resp = client.get(f'/api/analysis/{analysis_id}')
    assert get_resp.status_code == 200
    assert get_resp.json()['id'] == analysis_id

    original_resp = client.get(f'/api/analysis/{analysis_id}/original')
    assert original_resp.status_code == 200

    mask_resp = client.get(f'/api/analysis/{analysis_id}/mask')
    assert mask_resp.status_code == 200
    assert mask_resp.headers['content-type'] == 'image/png'

    overlay_resp = client.get(f'/api/analysis/{analysis_id}/overlay')
    assert overlay_resp.status_code == 200

    history_resp = client.get('/api/analysis/history')
    assert history_resp.status_code == 200
    assert history_resp.json()['total'] >= 1

    export_resp = client.get(f'/api/analysis/{analysis_id}/export?format=json')
    assert export_resp.status_code == 200
    assert export_resp.json()['id'] == analysis_id
    assert 'disclaimer' in export_resp.json()

    export_pdf_resp = client.get(f'/api/analysis/{analysis_id}/export?format=pdf')
    assert export_pdf_resp.status_code == 200
    assert export_pdf_resp.headers['content-type'] == 'application/pdf'

    delete_resp = client.delete(f'/api/analysis/{analysis_id}')
    assert delete_resp.status_code == 200
    assert delete_resp.json()['success'] is True

    get_after_delete = client.get(f'/api/analysis/{analysis_id}')
    assert get_after_delete.status_code == 404


def test_get_nonexistent_analysis_returns_404(client):
    resp = client.get('/api/analysis/does-not-exist')
    assert resp.status_code == 404


def test_predict_on_nonexistent_analysis_returns_404(client):
    resp = client.post('/api/analysis/predict/does-not-exist')
    assert resp.status_code == 404
