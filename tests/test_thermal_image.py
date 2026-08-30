import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.services.image.thermal import ThermalImageProcessor


def test_thermal_processor_creates_384px_monochrome_bitmap(tmp_path):
    source = tmp_path / "source.png"
    Image.new("RGB", (1024, 512), "white").save(source)

    result = ThermalImageProcessor().prepare(source)

    assert result.width == 384
    assert result.height == 192
    with Image.open(result.file) as image:
        assert image.size == (384, 192)
        assert image.mode == "1"
