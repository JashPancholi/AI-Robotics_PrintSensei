from PIL import Image, ImageDraw

from app.models.label_data import LabelData
from app.renderer.fonts import FontManager
from app.renderer.image_utils import draw_border, draw_wrapped_text, text_size
from app.renderer.qr import generate_qr_image
from app.renderer.templates.common import render_dynamic_template


def render_inventory_template(label_data: LabelData) -> Image.Image:
    return render_dynamic_template(label_data, _draw_inventory)


def _draw_inventory(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: FontManager,
    label_data: LabelData,
) -> int:
    margin = 18
    y = margin
    max_width = image.width - (margin * 2)
    title_font = fonts.get("large")
    body_font = fonts.get("small")

    y = draw_wrapped_text(draw, y, label_data.title.upper(), title_font, margin, max_width)
    y += 6

    shelf = label_data.metadata.get("shelf")
    if shelf:
        draw.text((margin, y), f"Shelf : {shelf}", fill="black", font=body_font)
        y += text_size(draw, f"Shelf : {shelf}", body_font)[1] + 8

    if label_data.quantity is not None:
        draw.text((margin, y), f"Qty : {label_data.quantity}", fill="black", font=body_font)
        y += text_size(draw, f"Qty : {label_data.quantity}", body_font)[1] + 12

    qr_value = label_data.qr_data or label_data.title
    y = _paste_qr(image, qr_value, y)
    draw_border(draw, image.width, image.height)
    return y


def _paste_qr(image: Image.Image, value: str, y: int) -> int:
    qr_image = generate_qr_image(value, size=112)
    image.paste(qr_image, ((image.width - qr_image.width) // 2, y))
    return y + qr_image.height
