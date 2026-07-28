from PIL import Image, ImageDraw

from app.models.label_data import LabelData
from app.renderer.fonts import FontManager
from app.renderer.image_utils import center_image, draw_centered_text, draw_wrapped_text
from app.renderer.qr import generate_qr_image
from app.renderer.templates.common import render_dynamic_template


def render_qr_template(label_data: LabelData) -> Image.Image:
    return render_dynamic_template(label_data, _draw_qr)


def _draw_qr(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: FontManager,
    label_data: LabelData,
) -> int:
    margin = 18
    y = margin
    data = label_data.qr_data or label_data.body or label_data.title

    y = draw_centered_text(draw, y, label_data.title or "Scan Me", fonts.get("medium"), image.width)
    y += 12
    y = center_image(image, generate_qr_image(data, size=132), y)
    y += 10
    return draw_wrapped_text(
        draw,
        y,
        data,
        fonts.get("tiny"),
        margin,
        image.width - (margin * 2),
    )
