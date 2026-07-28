from PIL import Image, ImageDraw

from app.models.label_data import LabelData
from app.renderer.fonts import FontManager
from app.renderer.image_utils import center_image, draw_centered_text, draw_wrapped_text
from app.renderer.qr import generate_qr_image
from app.renderer.templates.common import render_dynamic_template


def render_product_template(label_data: LabelData) -> Image.Image:
    return render_dynamic_template(label_data, _draw_product)


def _draw_product(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: FontManager,
    label_data: LabelData,
) -> int:
    margin = 18
    y = margin
    max_width = image.width - (margin * 2)
    y = draw_wrapped_text(draw, y, label_data.title, fonts.get("large"), margin, max_width)

    if label_data.price is not None:
        y += 4
        y = draw_centered_text(draw, y, f"Rs {label_data.price:g}", fonts.get("medium"), image.width)

    if label_data.date is not None:
        y += 8
        y = draw_centered_text(draw, y, label_data.date.isoformat(), fonts.get("tiny"), image.width)

    if label_data.body:
        y += 8
        y = draw_wrapped_text(draw, y, label_data.body, fonts.get("small"), margin, max_width)

    if label_data.qr_data:
        y += 10
        y = center_image(image, generate_qr_image(label_data.qr_data, size=104), y)

    return y
