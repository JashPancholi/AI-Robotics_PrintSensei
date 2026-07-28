from collections.abc import Callable

from PIL import Image, ImageDraw

from app.models.label_data import LabelData
from app.renderer.canvas import LabelCanvas
from app.renderer.fonts import FontManager

TemplateDrawer = Callable[[Image.Image, ImageDraw.ImageDraw, FontManager, LabelData], int]


def render_dynamic_template(label_data: LabelData, drawer: TemplateDrawer) -> Image.Image:
    height = 220
    while height <= 1200:
        canvas = LabelCanvas(height=height)
        image, draw = canvas.create()
        bottom = drawer(image, draw, FontManager(), label_data)
        if bottom + canvas.margin <= height:
            return image.crop((0, 0, canvas.width, bottom + canvas.margin))
        height += 120

    return image
