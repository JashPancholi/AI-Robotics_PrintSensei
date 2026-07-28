from collections.abc import Callable
from datetime import datetime
import logging
from pathlib import Path
import tkinter as tk

from PIL import Image, ImageDraw, ImageFont, ImageTk

from app.enums.device_state import DeviceState
from app.hardware.display.face import FaceRenderer
from app.hardware.menu.menu import Menu

logger = logging.getLogger(__name__)


class LCDSimulator:
    """Polished 320x240 embedded LCD simulator for the Pi appliance UI."""

    width = 320
    height = 240
    scale = 3
    background = "#111111"
    panel = "#161616"
    card = "#1B1B1B"
    card_light = "#242424"
    accent = "#2D8CFF"
    accent_dim = "#14395F"
    text = "#F7F7F7"
    muted = "#A7A7A7"
    success = "#39D98A"
    warning = "#FFCA3A"
    danger = "#FF5C5C"

    def __init__(self, face_renderer: FaceRenderer | None = None) -> None:
        self.face_renderer = face_renderer or FaceRenderer()
        self.font_tiny = _load_font(10)
        self.font_small = _load_font(12)
        self.font = _load_font(14)
        self.font_medium = _load_font(17)
        self.font_large = _load_font(24)
        self.frame = self._blank_frame()
        self.last_print_time: str | None = None
        self._root: tk.Tk | None = None
        self._label: tk.Label | None = None
        self._photo: ImageTk.PhotoImage | None = None

    def open_window(self, key_handler: Callable[[str], None] | None = None) -> None:
        self._root = tk.Tk()
        self._root.title("PrintSensei Simulator")
        self._root.resizable(False, False)
        self._root.configure(background=self.background)
        self._label = tk.Label(self._root, bd=0, highlightthickness=0)
        self._label.pack()
        if key_handler is not None:
            self._root.bind("<Key>", lambda event: key_handler(event.keysym))
        self._refresh_window()

    def run(self) -> None:
        if self._root is None:
            self.open_window()
        self._root.mainloop()

    def after(self, delay_ms: int, callback: Callable[[], None]) -> None:
        if self._root is None:
            callback()
            return
        self._root.after(delay_ms, callback)

    def render_boot(self, progress: float) -> Image.Image:
        logger.info("Screen transition: boot")
        image, draw = self._base_frame()
        self._draw_robot_avatar(draw, (134, 38), DeviceState.PROCESSING, size=52, blink=progress < 0.2)
        self._center_text(draw, "PrintSensei", 94, self.font_large)
        self._center_text(draw, "AI Robotic Workstation", 122, self.font_small, self.muted)
        y = 148
        for label, threshold in _boot_steps():
            step_progress = min(max((progress - (threshold - 0.34)) / 0.34, 0), 1)
            color = self.success if step_progress >= 1 else self.text
            self._draw_text(draw, (50, y), label, self.font_small, color)
            self._draw_segment_bar(draw, 190, y + 2, 80, step_progress)
            y += 22
        return image

    def render_ready(self) -> Image.Image:
        logger.info("Screen transition: ready")
        image, draw = self._base_frame()
        self._draw_card(draw, (24, 42, 296, 145))
        self._draw_robot_avatar(draw, (44, 58), DeviceState.READY, size=58)
        self._draw_text(draw, (126, 64), "Ready", self.font_large)
        self._draw_text(draw, (128, 96), "Press ENTER", self.font_medium, self.accent)
        self._draw_text(draw, (128, 120), "Physical buttons active", self.font_small, self.muted)
        self._draw_status_tiles(draw)
        self._draw_system_footer(draw)
        return image

    def render_listening(self, blink: bool = False) -> Image.Image:
        logger.info("Screen transition: listening")
        return self._render_expression("Listening", "Microphone ready", DeviceState.LISTENING, blink)

    def render_thinking(self, blink: bool = False) -> Image.Image:
        logger.info("Screen transition: thinking")
        return self._render_expression("Thinking", "Processing request", DeviceState.PROCESSING, blink)

    def render_scanning(self, blink: bool = False) -> Image.Image:
        logger.info("Screen transition: scanning")
        image, draw = self._base_frame()
        self._draw_card(draw, (34, 52, 286, 178))
        self._draw_robot_avatar(draw, (132, 70), DeviceState.LISTENING, size=56, blink=blink)
        self._draw_small_icon(draw, "camera", (150, 132), self.accent)
        self._center_text(draw, "Scanning", 152, self.font_medium, self.text)
        self._draw_footer(draw, "Camera module placeholder")
        return image

    def render_menu(self, menu: Menu) -> Image.Image:
        logger.info("Screen transition: menu")
        image, draw = self._base_frame()
        self._draw_text(draw, (20, 40), "MAIN MENU", self.font_medium, self.accent)
        y = 62
        for index, item in menu.visible_items(count=6):
            selected = index == menu.selected_index
            box = (18, y - 2, 302, y + 20)
            draw.rounded_rectangle(
                box,
                radius=8,
                fill=self.accent if selected else self.card,
                outline=self.accent_dim if not selected else self.accent,
            )
            fill = self.text if selected else self.muted
            self._draw_menu_icon(draw, item.title, (31, y + 4), fill)
            self._draw_text(draw, (58, y + 1), item.title, self.font_small, self.text)
            if selected:
                draw.rectangle((24, y + 4, 27, y + 14), fill=self.text)
            y += 24
        self._draw_footer(draw, "UP/DOWN Navigate     ENTER Select     ESC Back")
        return image

    def render_preview(
        self,
        title: str,
        details: list[str],
        confirm_index: int = 0,
        preview_file: Path | str | None = None,
    ) -> Image.Image:
        logger.info("Screen transition: preview")
        image, draw = self._base_frame()
        self._draw_text(draw, (20, 38), title, self.font_medium, self.accent)
        self._draw_card(draw, (22, 66, 298, 182))
        self._draw_thumbnail(image, draw, preview_file, (44, 76, 160, 172))
        y = 78
        for detail in details[:4]:
            self._draw_text(draw, (178, y), detail, self.font, self.text)
            y += 22
        self._draw_text(draw, (178, 164), "Preview ready", self.font_small, self.success)
        self._draw_footer(draw, "ENTER Print     ESC Cancel")
        return image

    def render_printing(self, progress: float) -> Image.Image:
        logger.info("Screen transition: printing")
        image, draw = self._base_frame()
        self._draw_card(draw, (30, 48, 290, 188))
        self._draw_printer_icon(draw, (132, 64))
        stage = _printing_stage(progress)
        self._center_text(draw, stage, 118, self.font_medium)
        self._draw_progress(draw, 58, 150, 204, progress)
        self._center_text(draw, f"{int(min(max(progress, 0), 1) * 100)}%", 174, self.font_small, self.muted)
        return image

    def render_done(self) -> Image.Image:
        logger.info("Screen transition: done")
        self.last_print_time = datetime.now().strftime("%H:%M")
        image, draw = self._base_frame()
        self._draw_check_icon(draw, (135, 54), 52)
        self._center_text(draw, "Label Printed", 124, self.font_large)
        self._center_text(draw, "Successfully", 154, self.font_medium, self.success)
        self._center_text(draw, "Returning to Ready", 188, self.font_small, self.muted)
        return image

    def render_error(self, message: str = "ERROR") -> Image.Image:
        logger.info("Screen transition: error")
        image, draw = self._base_frame()
        self._draw_warning_icon(draw, (135, 52), 52)
        self._center_text(draw, "Error", 116, self.font_large)
        self._center_text(draw, message, 148, self.font, self.muted)
        self._draw_footer(draw, "ESC Return")
        return image

    def render_placeholder(self, title: str, subtitle: str = "Coming soon") -> Image.Image:
        logger.info("Screen transition: placeholder %s", title)
        image, draw = self._base_frame()
        self._draw_card(draw, (28, 58, 292, 174))
        self._center_text(draw, title, 88, self.font_large, self.accent)
        self._center_text(draw, subtitle, 124, self.font, self.text)
        self._center_text(draw, "Reserved for future module", 150, self.font_small, self.muted)
        self._draw_footer(draw, "ESC Back")
        return image

    def render_camera_placeholder(self) -> Image.Image:
        return self.render_scanning()

    def render_ocr_placeholder(self) -> Image.Image:
        return self.render_placeholder("OCR")

    def render_voice_placeholder(self) -> Image.Image:
        return self.render_listening()

    def render_ai_placeholder(self) -> Image.Image:
        return self.render_thinking()

    def show(self, image: Image.Image) -> None:
        next_frame = image.convert("RGB")
        if self._label is not None:
            self._fade_to(next_frame)
            return
        self.frame = next_frame
        self._refresh_window()

    def _base_frame(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        image = self._blank_frame()
        draw = ImageDraw.Draw(image)
        self._draw_status_bar(draw)
        return image, draw

    def _blank_frame(self) -> Image.Image:
        return Image.new("RGB", (self.width, self.height), self.background)

    def _draw_status_bar(self, draw: ImageDraw.ImageDraw) -> None:
        draw.rounded_rectangle((6, 5, 314, 29), radius=8, fill="#0A0A0A")
        self._draw_robot_avatar(draw, (12, 9), DeviceState.READY, size=16)
        self._draw_text(draw, (33, 11), "PrintSensei", self.font_small)
        self._draw_status_chip(draw, (103, 10), "printer", "Ready", self.success)
        self._draw_status_chip(draw, (158, 10), "camera", "On", self.success)
        self._draw_status_chip(draw, (205, 10), "mic", "Ready", self.success)
        self._draw_text(draw, (268, 11), datetime.now().strftime("%H:%M"), self.font_small, self.muted)

    def _render_expression(
        self,
        title: str,
        subtitle: str,
        state: DeviceState,
        blink: bool = False,
    ) -> Image.Image:
        image, draw = self._base_frame()
        self._draw_card(draw, (34, 52, 286, 178))
        self._draw_robot_avatar(draw, (132, 70), state, size=56, blink=blink)
        self._center_text(draw, title, 136, self.font_large, self.accent)
        self._center_text(draw, subtitle, 166, self.font_small, self.muted)
        return image

    def _draw_status_chip(
        self,
        draw: ImageDraw.ImageDraw,
        position: tuple[int, int],
        icon: str,
        label: str,
        color: str,
    ) -> None:
        x, y = position
        self._draw_small_icon(draw, icon, (x, y + 1), color)
        self._draw_text(draw, (x + 13, y), label, self.font_tiny, self.muted)

    def _draw_status_tiles(self, draw: ImageDraw.ImageDraw) -> None:
        tiles = [
            ("Prints", "0", self.accent),
            ("Database", "Ready", self.success),
            ("Renderer", "Ready", self.success),
        ]
        x = 24
        for title, value, color in tiles:
            self._draw_card(draw, (x, 160, x + 84, 216), radius=8)
            self._draw_text(draw, (x + 10, 172), title, self.font_small, self.muted)
            self._draw_text(draw, (x + 10, 194), value, self.font, color)
            x += 94

    def _draw_system_footer(self, draw: ImageDraw.ImageDraw) -> None:
        last_print = self.last_print_time or "--:--"
        draw.rounded_rectangle((16, 222, 304, 238), radius=6, fill="#0A0A0A")
        self._draw_small_icon(draw, "network", (24, 224), self.success)
        self._draw_text(draw, (40, 224), "Connected", self.font_tiny, self.muted)
        self._draw_text(draw, (106, 224), "Jobs 0", self.font_tiny, self.muted)
        self._draw_small_icon(draw, "database", (158, 224), self.success)
        self._draw_text(draw, (174, 224), f"Last {last_print}", self.font_tiny, self.muted)
        self._draw_text(draw, (252, 224), "v1.0.0", self.font_tiny, self.muted)

    def _draw_footer(self, draw: ImageDraw.ImageDraw, text: str) -> None:
        draw.rounded_rectangle((8, 210, 312, 235), radius=8, fill="#0A0A0A")
        self._center_text(draw, text, 218, self.font_tiny, self.muted)

    def _draw_card(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        radius: int = 12,
    ) -> None:
        draw.rounded_rectangle(box, radius=radius, fill=self.card, outline="#2D2D2D")

    def _draw_robot_avatar(
        self,
        draw: ImageDraw.ImageDraw,
        position: tuple[int, int],
        state: DeviceState,
        size: int = 44,
        blink: bool = False,
    ) -> None:
        x, y = position
        if size < 24:
            draw.rounded_rectangle((x, y + 3, x + size, y + size), radius=4, fill=self.card_light, outline=self.accent)
            if blink:
                draw.line((x + 4, y + 10, x + 7, y + 10), fill=self.text)
                draw.line((x + size - 7, y + 10, x + size - 4, y + 10), fill=self.text)
            else:
                draw.ellipse((x + 4, y + 8, x + 7, y + 11), fill=self.text)
                draw.ellipse((x + size - 7, y + 8, x + size - 4, y + 11), fill=self.text)
            draw.line((x + 5, y + 14, x + size - 5, y + 14), fill=self.success, width=1)
            return
        expression = self.face_renderer.face_for(state)
        draw.rounded_rectangle((x, y + size // 5, x + size, y + size), radius=size // 6, fill=self.card_light, outline=self.accent)
        draw.rectangle((x + size // 2 - 1, y + 2, x + size // 2 + 1, y + size // 5), fill=self.accent)
        draw.ellipse((x + size // 2 - 4, y, x + size // 2 + 4, y + 8), fill=self.accent)
        eye_y = y + size // 2
        if expression == "thinking":
            draw.line((x + 13, eye_y, x + 22, eye_y), fill=self.text, width=2)
            draw.line((x + size - 22, eye_y, x + size - 13, eye_y), fill=self.text, width=2)
        elif expression == "error":
            draw.line((x + 13, eye_y - 3, x + 21, eye_y + 5), fill=self.danger, width=2)
            draw.line((x + 21, eye_y - 3, x + 13, eye_y + 5), fill=self.danger, width=2)
            draw.line((x + size - 21, eye_y - 3, x + size - 13, eye_y + 5), fill=self.danger, width=2)
            draw.line((x + size - 13, eye_y - 3, x + size - 21, eye_y + 5), fill=self.danger, width=2)
        else:
            if blink:
                draw.line((x + 14, eye_y + 1, x + 22, eye_y + 1), fill=self.text, width=2)
                draw.line((x + size - 22, eye_y + 1, x + size - 14, eye_y + 1), fill=self.text, width=2)
            else:
                draw.ellipse((x + 14, eye_y - 3, x + 22, eye_y + 5), fill=self.text)
                draw.ellipse((x + size - 22, eye_y - 3, x + size - 14, eye_y + 5), fill=self.text)
        mouth_y = y + size - 14
        if expression == "printing":
            draw.arc((x + 18, mouth_y - 6, x + size - 18, mouth_y + 8), 0, 180, fill=self.success, width=2)
        elif expression == "listening":
            draw.ellipse((x + size // 2 - 4, mouth_y - 2, x + size // 2 + 4, mouth_y + 6), outline=self.accent, width=2)
        elif expression == "error":
            draw.line((x + 20, mouth_y + 4, x + size - 20, mouth_y - 2), fill=self.danger, width=2)
        else:
            draw.arc((x + 18, mouth_y - 8, x + size - 18, mouth_y + 6), 0, 180, fill=self.success, width=2)

    def _draw_small_icon(
        self,
        draw: ImageDraw.ImageDraw,
        icon: str,
        position: tuple[int, int],
        color: str,
    ) -> None:
        x, y = position
        if icon == "printer":
            draw.rectangle((x, y + 5, x + 10, y + 11), outline=color)
            draw.rectangle((x + 2, y, x + 8, y + 5), fill=color)
        elif icon == "camera":
            draw.rectangle((x, y + 3, x + 11, y + 11), outline=color)
            draw.ellipse((x + 4, y + 5, x + 8, y + 9), outline=color)
        elif icon == "mic":
            draw.rounded_rectangle((x + 3, y, x + 8, y + 9), radius=3, outline=color)
            draw.line((x + 5, y + 9, x + 5, y + 12), fill=color)
            draw.line((x + 2, y + 12, x + 9, y + 12), fill=color)
        elif icon == "network":
            draw.arc((x, y + 2, x + 12, y + 14), 210, 330, fill=color, width=1)
            draw.arc((x + 3, y + 5, x + 9, y + 13), 210, 330, fill=color, width=1)
            draw.ellipse((x + 5, y + 11, x + 7, y + 13), fill=color)
        elif icon == "database":
            draw.ellipse((x, y, x + 11, y + 4), outline=color)
            draw.rectangle((x, y + 2, x + 11, y + 11), outline=color)
            draw.arc((x, y + 7, x + 11, y + 11), 0, 180, fill=color)

    def _draw_menu_icon(
        self,
        draw: ImageDraw.ImageDraw,
        title: str,
        position: tuple[int, int],
        color: str,
    ) -> None:
        x, y = position
        if title == "Study Label":
            draw.rectangle((x, y, x + 6, y + 12), outline=color)
            draw.rectangle((x + 7, y, x + 13, y + 12), outline=color)
            draw.line((x + 2, y + 3, x + 5, y + 3), fill=color)
        elif title == "Inventory Label":
            draw.polygon([(x, y + 4), (x + 7, y), (x + 14, y + 4), (x + 7, y + 8)], outline=color)
            draw.rectangle((x, y + 4, x + 14, y + 13), outline=color)
        elif title == "QR Label":
            for dx, dy in [(0, 0), (9, 0), (0, 9)]:
                draw.rectangle((x + dx, y + dy, x + dx + 5, y + dy + 5), outline=color)
            draw.rectangle((x + 9, y + 9, x + 13, y + 13), fill=color)
        elif title == "Product Label":
            draw.rounded_rectangle((x, y + 1, x + 14, y + 12), radius=3, outline=color)
            draw.ellipse((x + 3, y + 4, x + 5, y + 6), fill=color)
        elif title == "History":
            draw.ellipse((x, y, x + 13, y + 13), outline=color)
            draw.line((x + 7, y + 7, x + 7, y + 3), fill=color)
            draw.line((x + 7, y + 7, x + 10, y + 9), fill=color)
        elif title == "Settings":
            draw.ellipse((x + 2, y + 2, x + 12, y + 12), outline=color)
            draw.ellipse((x + 5, y + 5, x + 9, y + 9), outline=color)

    def _draw_printer_icon(self, draw: ImageDraw.ImageDraw, position: tuple[int, int]) -> None:
        x, y = position
        draw.rounded_rectangle((x, y + 18, x + 56, y + 48), radius=6, fill=self.card_light, outline=self.accent)
        draw.rectangle((x + 10, y, x + 46, y + 20), fill="#EDEDED")
        draw.rectangle((x + 10, y + 36, x + 46, y + 58), fill="#FFFFFF")
        draw.ellipse((x + 42, y + 27, x + 48, y + 33), fill=self.success)

    def _draw_check_icon(self, draw: ImageDraw.ImageDraw, position: tuple[int, int], size: int) -> None:
        x, y = position
        draw.ellipse((x, y, x + size, y + size), fill=self.success)
        draw.line((x + 14, y + 28, x + 24, y + 38, x + 40, y + 17), fill="#0B2818", width=5)

    def _draw_warning_icon(self, draw: ImageDraw.ImageDraw, position: tuple[int, int], size: int) -> None:
        x, y = position
        points = [(x + size // 2, y), (x + size, y + size), (x, y + size)]
        draw.polygon(points, fill=self.warning)
        self._center_text(draw, "!", y + 19, self.font_large, "#2A2100")

    def _draw_progress(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        progress: float,
    ) -> None:
        progress = min(max(progress, 0.0), 1.0)
        draw.rounded_rectangle((x, y, x + width, y + 14), radius=7, fill="#0A0A0A", outline="#303030")
        fill_width = max(0, int(width * progress))
        if fill_width:
            draw.rounded_rectangle((x, y, x + fill_width, y + 14), radius=7, fill=self.accent)

    def _draw_segment_bar(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        width: int,
        progress: float,
    ) -> None:
        segments = 10
        gap = 2
        segment_width = (width - (gap * (segments - 1))) // segments
        filled = round(min(max(progress, 0.0), 1.0) * segments)
        for index in range(segments):
            left = x + index * (segment_width + gap)
            fill = self.accent if index < filled else "#2C2C2C"
            draw.rounded_rectangle((left, y, left + segment_width, y + 8), radius=2, fill=fill)

    def _draw_thumbnail(
        self,
        image: Image.Image,
        draw: ImageDraw.ImageDraw,
        preview_file: Path | str | None,
        box: tuple[int, int, int, int],
    ) -> None:
        draw.rounded_rectangle(box, radius=8, fill="#F4F4F4")
        if preview_file is None or not Path(preview_file).exists():
            self._center_text(draw, "Preview", 118, self.font, fill=self.muted)
            return
        with Image.open(preview_file) as source:
            thumbnail = source.convert("RGB")
            thumbnail.thumbnail((box[2] - box[0] - 10, box[3] - box[1] - 10), Image.Resampling.LANCZOS)
        x = box[0] + ((box[2] - box[0] - thumbnail.width) // 2)
        y = box[1] + ((box[3] - box[1] - thumbnail.height) // 2)
        image.paste(thumbnail, (x, y))

    def _draw_text(
        self,
        draw: ImageDraw.ImageDraw,
        position: tuple[int, int],
        text: str,
        font: ImageFont.ImageFont,
        fill: str | None = None,
    ) -> None:
        draw.text(position, _safe_text(text), font=font, fill=fill or self.text)

    def _center_text(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        y: int,
        font: ImageFont.ImageFont,
        fill: str | None = None,
    ) -> None:
        safe = _safe_text(text)
        bbox = draw.textbbox((0, 0), safe, font=font)
        x = max((self.width - (bbox[2] - bbox[0])) // 2, 0)
        draw.text((x, y), safe, font=font, fill=fill or self.text)

    def _refresh_window(self) -> None:
        if self._label is None:
            return
        scaled = self.frame.resize(
            (self.width * self.scale, self.height * self.scale),
            Image.Resampling.NEAREST,
        )
        self._photo = ImageTk.PhotoImage(scaled)
        self._label.configure(image=self._photo)

    def _fade_to(self, next_frame: Image.Image) -> None:
        start = self.frame
        steps = 4

        def render_step(step: int) -> None:
            if step > steps:
                self.frame = next_frame
                self._refresh_window()
                return
            self.frame = Image.blend(start, next_frame, step / steps)
            self._refresh_window()
            if self._root is not None:
                self._root.after(30, lambda: render_step(step + 1))

        render_step(1)


def _load_font(size: int) -> ImageFont.ImageFont:
    for font_name in ["arial.ttf", "DejaVuSans.ttf"]:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _safe_text(value: str) -> str:
    try:
        value.encode("latin-1")
        return value
    except UnicodeEncodeError:
        return value.encode("latin-1", errors="replace").decode("latin-1")


def _boot_message(progress: float) -> str:
    if progress < 0.34:
        return "Loading Renderer"
    if progress < 0.67:
        return "Loading Database"
    return "Initializing Hardware"


def _boot_steps() -> list[tuple[str, float]]:
    return [
        ("Loading Renderer...", 0.34),
        ("Loading Database...", 0.67),
        ("Initializing Hardware...", 1.0),
    ]


def _printing_stage(progress: float) -> str:
    if progress < 0.25:
        return "Preparing..."
    if progress < 0.55:
        return "Rendering..."
    if progress < 0.9:
        return "Sending to Printer..."
    return "Completed"

