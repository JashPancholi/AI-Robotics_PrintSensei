import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.public_main import app


def test_public_app_exposes_health_but_not_private_apis_or_docs():
    client = TestClient(app)

    assert client.get("/health").status_code == 200
    assert client.get("/api/history").status_code == 404
    assert client.post("/api/study/jobs", json={"text": "test"}).status_code == 404
    assert client.post("/api/shares/example/print").status_code == 404
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404
