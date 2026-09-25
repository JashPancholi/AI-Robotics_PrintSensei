"""TSPL encoding and transport for thermal label printers."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

from PIL import Image


@dataclass(frozen=True)
class PrinterConfig:
    """Runtime configuration; environment variables make Pi deployment configurable."""

    device: str = os.getenv("PRINTER_DEVICE", "/dev/usb/lp0")
    cups_queue: str = os.getenv("CUPS_QUEUE", "POSIFLOW58D")
    use_cups: bool = os.getenv("PRINTER_USE_CUPS", "false").lower() in {"1", "true", "yes"}


def pil_to_tspl_bitmap(image: Image.Image, x: int = 0, y: int = 0) -> bytes:
    """Encode an image as the binary data portion of a TSPL ``BITMAP`` command."""
    image = image.convert("1")
    width, height = image.size
    padded_width = (width + 7) // 8 * 8
    if padded_width != width:
        padded = Image.new("1", (padded_width, height), 255)
        padded.paste(image)
        image = padded
        width = padded_width

    width_bytes = width // 8
    packed = bytearray()
    pixels = image.load()
    for row in range(height):
        for byte_column in range(width_bytes):
            value = 0
            for bit in range(8):
                if pixels[byte_column * 8 + bit, row] == 0:
                    value |= 1 << (7 - bit)
            packed.append(value)

    command = f"BITMAP {x},{y},{width_bytes},{height},0,".encode("ascii")
    return command + bytes(packed) + b"\r\n"


def send_to_printer(payload: bytes, config: PrinterConfig | None = None) -> tuple[bool, str]:
    """Write a raw TSPL payload to USB, with an optional raw CUPS fallback."""
    config = config or PrinterConfig()
    try:
        if not config.use_cups and os.path.exists(config.device):
            with open(config.device, "wb") as printer:
                printer.write(payload)
                printer.flush()
            return True, "Sent to printer via direct USB"

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
    except OSError as exc:
        return False, str(exc)


def print_label(
    image: Image.Image,
    width_mm: int = 50,
    height_mm: int = 50,
    gap_mm: int = 2,
    config: PrinterConfig | None = None,
) -> tuple[bool, str]:
    """Create one TSPL label and send it to the configured printer."""
    header = (
        f"SIZE {width_mm} mm,{height_mm} mm\r\n"
        f"GAP {gap_mm} mm,0 mm\r\n"
        "DIRECTION 1,0\r\n"
        "REFERENCE 0,0\r\n"
        "CLS\r\n"
    ).encode("ascii")
    payload = header + pil_to_tspl_bitmap(image) + b"\r\nPRINT 1\r\nTEAR\r\n"
    return send_to_printer(payload, config)
