from PIL import Image, ImageDraw, ImageFont, ImageOps


def text_size(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    if not text:
        return []

    lines: list[str] = []
    for paragraph in text.splitlines():
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if text_size(draw, candidate, font)[0] <= max_width:
                current = candidate
            else:
                lines.extend(_break_long_line(draw, current, font, max_width))
                current = word

        lines.extend(_break_long_line(draw, current, font, max_width))

    return lines


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str,
    font: ImageFont.ImageFont,
    canvas_width: int,
) -> int:
    width, height = text_size(draw, text, font)
    x = max((canvas_width - width) // 2, 0)
    draw.text((x, y), text, fill="black", font=font)
    return y + height


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    y: int,
    text: str | None,
    font: ImageFont.ImageFont,
    x: int,
    max_width: int,
    line_gap: int = 6,
) -> int:
    for line in wrap_text(draw, text or "", font, max_width):
        draw.text((x, y), line, fill="black", font=font)
        y += text_size(draw, line or " ", font)[1] + line_gap
    return y


def center_image(base: Image.Image, overlay: Image.Image, y: int) -> int:
    x = (base.width - overlay.width) // 2
    base.paste(overlay, (x, y))
    return y + overlay.height


def draw_border(draw: ImageDraw.ImageDraw, width: int, height: int) -> None:
    draw.rectangle((0, 0, width - 1, height - 1), outline="black", width=2)


def grayscale(image: Image.Image) -> Image.Image:
    return ImageOps.grayscale(image)


def threshold(image: Image.Image, cutoff: int = 180) -> Image.Image:
    return grayscale(image).point(lambda pixel: 255 if pixel > cutoff else 0, mode="1")


def add_padding(image: Image.Image, padding: int, fill: str = "white") -> Image.Image:
    return ImageOps.expand(image, border=padding, fill=fill)


def _break_long_line(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    if text_size(draw, text, font)[0] <= max_width:
        return [text]

    lines: list[str] = []
    current = ""
    for char in text:
        candidate = f"{current}{char}"
        if current and text_size(draw, candidate, font)[0] > max_width:
            lines.append(current)
            current = char
        else:
            current = candidate

    if current:
        lines.append(current)
    return lines
