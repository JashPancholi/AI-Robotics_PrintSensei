import base64
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.printer import pil_to_escpos_raster


def test_escpos_header_and_black_bits():
    """Verify that ESC/POS payload begins with GS v 0 and correctly packs black bits."""
    image = Image.new("1", (8, 2), 255)
    image.putpixel((0, 0), 0)  # Top-left black pixel -> MSB bit 7 of byte 0
    image.putpixel((7, 1), 0)  # Bottom-right black pixel -> LSB bit 0 of byte 1

    payload = pil_to_escpos_raster(image)

    # GS v 0 header: 0x1D, 0x76, 0x30, 0x00
    assert payload.startswith(b"\x1d\x76\x30\x00")
    # Header format: GS v 0 \x00 xL xH yL yH
    # For width=8 (width_bytes=1) and height=2: xL=1, xH=0, yL=2, yH=0
    assert payload[:8] == b"\x1d\x76\x30\x00\x01\x00\x02\x00"
    # Row 0: 0b10000000 (0x80), Row 1: 0b00000001 (0x01)
    assert payload[8:] == bytes([0b10000000, 0b00000001])


def test_escpos_encoder_pads_width():
    """Verify that images with width not divisible by 8 are padded to a multiple of 8."""
    image = Image.new("1", (9, 1), 255)
    image.putpixel((0, 0), 0)  # First pixel black
    image.putpixel((8, 0), 0)  # 9th pixel black (in second byte)

    payload = pil_to_escpos_raster(image)

    # Padded width is 16 -> width_bytes=2
    assert payload[:8] == b"\x1d\x76\x30\x00\x02\x00\x01\x00"
    # Byte 0: 0b10000000, Byte 1: 0b10000000 (padding bits on right are 0)
    assert payload[8:] == bytes([0b10000000, 0b10000000])


def test_escpos_dimension_bytes_match_image():
    """Verify width and height bytes for larger dimensions (e.g. 384x200)."""
    image = Image.new("1", (384, 200), 255)
    payload = pil_to_escpos_raster(image)

    # width_bytes = 384 // 8 = 48 (0x30, 0x00), height = 200 (0xC8, 0x00)
    assert payload[:8] == b"\x1d\x76\x30\x00\x30\x00\xc8\x00"
    assert len(payload) == 8 + (48 * 200)


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

