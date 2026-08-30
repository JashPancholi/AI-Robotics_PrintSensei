from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageOps


@dataclass(frozen=True)
class ThermalImageResult:
    file: Path
    width: int
    height: int


class ThermalImageProcessor:
    """Converts generated artwork into the bitmap dimensions the printer will use."""

    def __init__(self, target_width: int = 384, threshold: int = 200) -> None:
        self.target_width = target_width
        self.threshold = threshold

    def prepare(self, source: Path | str) -> ThermalImageResult:
        source_path = Path(source)
        output_path = source_path.with_name(f"{source_path.stem}_thermal.png")

        with Image.open(source_path) as image:
            grayscale = ImageOps.autocontrast(ImageOps.grayscale(image))
            target_height = max(1, round(grayscale.height * self.target_width / grayscale.width))
            resized = grayscale.resize(
                (self.target_width, target_height),
                Image.Resampling.LANCZOS,
            )
            monochrome = resized.point(
                lambda pixel: 255 if pixel >= self.threshold else 0,
                mode="1",
            )
            monochrome.save(output_path, format="PNG")

        return ThermalImageResult(
            file=output_path,
            width=self.target_width,
            height=target_height,
        )
