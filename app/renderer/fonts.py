from functools import lru_cache
from pathlib import Path

from PIL import ImageFont


class FontManager:
    def __init__(self, font_dir: Path | None = None) -> None:
        self.font_dir = font_dir or Path("app/assets/fonts")

    @lru_cache(maxsize=8)
    def get(self, size: str) -> ImageFont.ImageFont:
        sizes = {
            "large": 32,
            "medium": 22,
            "small": 18,
            "tiny": 14,
        }
        point_size = sizes.get(size, sizes["small"])

        for font_name in ["arial.ttf", "DejaVuSans.ttf"]:
            try:
                return ImageFont.truetype(font_name, point_size)
            except OSError:
                continue

        return ImageFont.load_default()
