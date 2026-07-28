from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from app.enums.label_type import LabelType
from app.models.label_data import LabelData
from app.renderer.templates import (
    render_inventory_template,
    render_product_template,
    render_qr_template,
    render_study_template,
)


@dataclass(frozen=True)
class RenderResult:
    status: str
    file: str
    width: int
    height: int


class LabelRenderer:
    def __init__(self, output_dir: Path | str = "generated_labels") -> None:
        self.output_dir = Path(output_dir)

    def render(self, label_data: LabelData) -> RenderResult:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        image = self._render_image(label_data)
        file_path = self._next_file_path()
        image.save(file_path, format="PNG")

        return RenderResult(
            status="success",
            file=file_path.as_posix(),
            width=image.width,
            height=image.height,
        )

    def _render_image(self, label_data: LabelData) -> Image.Image:
        label_type = label_data.label_type
        if label_data.template:
            label_type = LabelType(label_data.template)

        if label_type is LabelType.INVENTORY:
            return render_inventory_template(label_data)
        if label_type is LabelType.QR:
            return render_qr_template(label_data)
        if label_type is LabelType.STUDY:
            return render_study_template(label_data)
        if label_type is LabelType.PRODUCT:
            return render_product_template(label_data)

        return render_qr_template(label_data)

    def _next_file_path(self) -> Path:
        existing_numbers = []
        for path in self.output_dir.glob("label_*.png"):
            try:
                existing_numbers.append(int(path.stem.split("_")[1]))
            except (IndexError, ValueError):
                continue

        next_number = (max(existing_numbers) + 1) if existing_numbers else 1
        return self.output_dir / f"label_{next_number:05d}.png"
