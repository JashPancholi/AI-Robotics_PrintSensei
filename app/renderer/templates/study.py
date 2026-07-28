from PIL import Image, ImageDraw

from app.models.label_data import LabelData
from app.renderer.fonts import FontManager
from app.renderer.image_utils import center_image, draw_wrapped_text
from app.renderer.qr import generate_qr_image
from app.renderer.templates.common import render_dynamic_template


def render_study_template(label_data: LabelData) -> Image.Image:
    return render_dynamic_template(label_data, _draw_study)


def _draw_study(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: FontManager,
    label_data: LabelData,
) -> int:
    margin = 18
    max_width = image.width - (margin * 2)
    y = margin
    y = draw_wrapped_text(draw, y, label_data.title, fonts.get("medium"), margin, max_width)
    y += 8

    points = label_data.metadata.get("points")
    if isinstance(points, list):
        body = "\n".join(f"- {point}" for point in points)
    else:
        body = label_data.body or label_data.subtitle or ""
    y = draw_wrapped_text(draw, y, body, fonts.get("small"), margin, max_width)

    if label_data.qr_data:
        y += 8
        y = center_image(image, generate_qr_image(label_data.qr_data, size=104), y)

    return y
