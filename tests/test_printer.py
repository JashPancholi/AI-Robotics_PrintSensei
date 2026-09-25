import base64
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.printer import pil_to_tspl_bitmap


def test_tspl_encoder_pads_width_and_uses_black_bits():
    image = Image.new("1", (9, 1), 255)
    image.putpixel((0, 0), 0)
    image.putpixel((8, 0), 0)

    payload = pil_to_tspl_bitmap(image)

    assert payload.startswith(b"BITMAP 0,0,2,1,0,")
    assert payload.endswith(bytes([0b10000000, 0b10000000]) + b"\r\n")


def test_print_endpoint_decodes_data_uri_and_returns_printer_result(monkeypatch):
    image = Image.new("RGB", (8, 8), "white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    data_uri = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
    calls = []

    def fake_print(decoded, width, height, gap):
        calls.append((decoded.size, width, height, gap))
        return True, "Sent to test printer"

    monkeypatch.setattr("app.routers.print_label", fake_print)
    response = TestClient(app).post("/api/print", json={"image_base64": data_uri})

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert calls == [((8, 8), 50, 50, 2)]


def test_print_endpoint_rejects_invalid_image():
    response = TestClient(app).post("/api/print", json={"image_base64": "not base64"})
    assert response.status_code == 422
