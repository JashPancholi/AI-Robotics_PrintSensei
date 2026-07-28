import sys
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.enums.label_type import LabelType
from app.models.label_data import LabelData
from app.renderer import LabelRenderer
from app.main import app

client = TestClient(app)


def test_inventory_template_creates_384_pixel_png(tmp_path):
    result = LabelRenderer(tmp_path).render(
        LabelData(
            title="Arduino Uno",
            quantity=12,
            qr_data="inventory:arduino-uno",
            label_type=LabelType.INVENTORY,
            metadata={"shelf": "B2"},
        )
    )

    assert_rendered_png(result.file)


def test_qr_template_handles_very_long_urls(tmp_path):
    result = LabelRenderer(tmp_path).render(
        LabelData(
            title="Scan Me",
            qr_data="https://github.com/pranshu/printsensei/tree/main/docs/very/long/path",
            label_type=LabelType.QR,
        )
    )

    assert_rendered_png(result.file)


def test_study_template_handles_unicode_values(tmp_path):
    result = LabelRenderer(tmp_path).render(
        LabelData(
            title="Binary Search",
            body="Sorted array\nO(log n)\nDivide and conquer\nHindi: नमस्ते",
            qr_data="https://example.com/study/binary-search",
            label_type=LabelType.STUDY,
        )
    )

    assert_rendered_png(result.file)


def test_product_template_handles_empty_optional_values(tmp_path):
    result = LabelRenderer(tmp_path).render(
        LabelData(title="Coffee", label_type=LabelType.PRODUCT)
    )

    assert_rendered_png(result.file)


def test_inventory_template_handles_long_values(tmp_path):
    result = LabelRenderer(tmp_path).render(
        LabelData(
            title="Arduino Uno compatible robotics controller board with headers",
            quantity=999,
            label_type=LabelType.INVENTORY,
            metadata={"shelf": "Back Room Shelf B2 - Top Rack"},
        )
    )

    assert_rendered_png(result.file)


def test_render_endpoint_creates_label_file():
    response = client.post(
        "/render",
        json={"title": "Arduino Uno", "quantity": 12, "shelf": "B2"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["file"].startswith("generated_labels/label_")
    assert_rendered_png(body["file"])


def assert_rendered_png(file_path: str) -> None:
    path = Path(file_path)
    assert path.exists()

    with Image.open(path) as image:
        assert image.format == "PNG"
        assert image.width == 384
        assert image.height > 0
