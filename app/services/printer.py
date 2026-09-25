"""ESC/POS raster encoding and transport for thermal label printers."""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass

from PIL import Image

from shared.config import HARDWARE_MODE


@dataclass(frozen=True)
class PrinterConfig:
    """Runtime configuration; environment variables make Pi deployment configurable."""

    device: str = os.getenv("PRINTER_DEVICE", "/dev/usb/lp0")
    cups_queue: str = os.getenv("CUPS_QUEUE", "POSIFLOW58D")
    use_cups: bool = os.getenv("PRINTER_USE_CUPS", "false").lower() in {"1", "true", "yes"}


def pil_to_escpos_raster(image: Image.Image) -> bytes:
    """Encode an image into ESC/POS GS v 0 raster payload."""
    image = image.convert("1")
    width, height = image.size

    padded_width = (width + 7) // 8 * 8
    if padded_width != width:
        padded = Image.new("1", (padded_width, height), 255)
        padded.paste(image, (0, 0))
        image = padded
        width = padded_width

    width_bytes = width // 8
    header = (
        b"\x1d\x76\x30\x00"
        + bytes([
            width_bytes & 0xFF,
            (width_bytes >> 8) & 0xFF,
            height & 0xFF,
            (height >> 8) & 0xFF,
        ])
    )

    packed = bytearray()
    pixels = image.load()
    for row in range(height):
        for byte_column in range(width_bytes):
            value = 0
            for bit in range(8):
                if pixels[byte_column * 8 + bit, row] == 0:
                    value |= 1 << (7 - bit)
            packed.append(value)

    return header + bytes(packed)


def send_to_printer(payload: bytes, config: PrinterConfig | None = None) -> tuple[bool, str]:
    """Write raw ESC/POS bytes to direct USB (/dev/usb/lp0), or CUPS as fallback."""
    config = config or PrinterConfig()
    try:
        if not config.use_cups and os.path.exists(config.device):
            with open(config.device, "wb") as printer:
                printer.write(payload)
                printer.flush()
            return True, "Sent to printer via direct USB"

        if shutil.which("lp"):
            result = subprocess.run(
                ["lp", "-d", config.cups_queue, "-o", "raw"],
                input=payload,
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                return True, "Sent to printer via CUPS"
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            return False, detail or "CUPS rejected the print job"

        # On non-Linux/PC simulator environments without direct USB or lp:
        if HARDWARE_MODE == "pc" or os.environ.get("MOCK_PRINTER", "").lower() in {"1", "true"}:
            return True, "Simulated print (PC mode): ESC/POS raster payload generated successfully"

        return False, f"Printer device not found at {config.device} and CUPS 'lp' unavailable"
    except OSError as exc:
        return False, str(exc)


def print_label(
    image: Image.Image,
    label_width_mm: int = 50,
    label_height_mm: int = 50,
    gap_mm: int = 2,
    config: PrinterConfig | None = None,
) -> tuple[bool, str]:
    """Encode image with ESC/POS GS v 0 raster and send to the POSIFLOW 58D printer."""
    raster_data = pil_to_escpos_raster(image)
    payload = raster_data + b"\n\n\n"
    return send_to_printer(payload, config)

