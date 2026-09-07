import base64
from pathlib import Path
from typing import Union
from openai import OpenAI
from dotenv import load_dotenv

from .models import VisualAnalysis

load_dotenv()


class VisionService:
    def __init__(self, client: OpenAI = None):
        self.client = client or OpenAI()

    def analyze(self, image_input: Union[str, Path]) -> VisualAnalysis:
        raw_str = str(image_input).strip()
        image_b64 = None
        mime_type = "image/jpeg"

        # Case 1: Browser Data URI (e.g. data:image/png;base64,...)
        if raw_str.startswith("data:image"):
            header, _, encoded = raw_str.partition(",")
            image_b64 = encoded
            if ":" in header and ";" in header:
                mime_type = header.split(":", 1)[1].split(";", 1)[0]

        # Case 2: Local file path on disk
        # Guard with length check (< 4096) to prevent Windows OSError on raw base64 strings
        elif len(raw_str) < 4096 and (Path(raw_str).is_file() or Path(raw_str).resolve().is_file()):
            target_path = Path(raw_str) if Path(raw_str).is_file() else Path(raw_str).resolve()
            suffix = target_path.suffix.lower().lstrip(".")
            if suffix in ("jpg", "jpeg"):
                mime_type = "image/jpeg"
            elif suffix == "png":
                mime_type = "image/png"
            elif suffix == "webp":
                mime_type = "image/webp"

            with open(target_path, "rb") as file:
                image_b64 = base64.b64encode(file.read()).decode("utf-8")

        # Case 3: Already raw base64
        else:
            image_b64 = raw_str

        # Clean trailing whitespace / newlines
        image_b64 = image_b64.strip()

        # Call OpenAI Structured Outputs with gpt-4o-mini
        response = self.client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert OCR and visual perception system for PrintSensei. "
                        "Thoroughly analyze the image. Extract every line of visible text, handwriting, "
                        "mathematical formulas, diagram structures, flowcharts, and components. "
                        "Identify spatial connections, arrows, hierarchies, and labels accurately."
                    ),
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "Extract all legible text, diagram flow, and visual components "
                                "from this image for study notes generation."
                            ),
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_b64}",
                                "detail": "high",
                            },
                        },
                    ],
                },
            ],
            response_format=VisualAnalysis,
        )

        return response.choices[0].message.parsed