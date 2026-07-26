import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.main import app

client = TestClient(app)


def test_home_endpoint_returns_status():
    response = client.get("/")
    assert response.status_code == 200
    assert "PrintSensei is Running" in response.text
