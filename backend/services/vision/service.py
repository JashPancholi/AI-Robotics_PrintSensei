import base64
import os
from pathlib import Path
from typing import Union
from openai import OpenAI
from dotenv import load_dotenv

from backend.services.ai.openrouter_provider import (
    OPENROUTER_BASE_URL,
    _default_headers,
    extract_json,
)
from .models import VisualAnalysis

load_dotenv()

DEFAULT_VISION_MODEL = "minimax/minimax-m3:free"

_SYSTEM_PROMPT = (
    "You are an expert visual perception model for PrintSensei. "
    "Analyze the image and extract OCR text, visual components, "
    "their spatial arrangements, and relationships. Return ONLY JSON."
)


def _default_provider_name() -> str:
    """Prefer OpenRouter when its key is present (OpenAI creds are empty).

    Explicit override via VISION_PROVIDER=openai|openrouter.
    """
    explicit = os.getenv("VISION_PROVIDER", "").strip().lower()
    if explicit in ("openai", "openrouter"):
        return explicit
    if os.getenv("OPENROUTER_API_KEY"):
        return "openrouter"
    return "openai"


class VisionService:
    def __init__(self, client: OpenAI = None, model: str | None = None):
        if client is not None:
            self.client = client
            self.model = model or "gpt-4.1-mini"
            self._strict_parse = True
            return

        provider = _default_provider_name()
        if provider == "openrouter":
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise ValueError(
                    "OPENROUTER_API_KEY is not set. "
                    "Get a free key at https://openrouter.ai/keys."
                )
            self.client = OpenAI(
                base_url=os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
                api_key=api_key,
                default_headers=_default_headers(),
            )
            self.model = model or os.getenv("OPENROUTER_VISION_MODEL", DEFAULT_VISION_MODEL)
            self._strict_parse = False
        else:
            self.client = OpenAI()
            self.model = model or "gpt-4.1-mini"
            self._strict_parse = True
        # Same 402 reservation issue as text: cap output tokens so free
        # models work on fresh accounts with no paid credits.
        self.max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "2048"))

    def analyze(self, image_input: Union[str, Path]) -> VisualAnalysis:
        # 1. Handle file path or raw base64 string
        if isinstance(image_input, (str, Path)) and Path(image_input).is_file():
            with open(image_input, "rb") as file:
                image_data = base64.b64encode(file.read()).decode("utf-8")
        else:
            image_data = str(image_input)

        messages = [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract all structural details from this image."},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }
        ]

        # 2a. OpenAI path: native structured outputs.
        if self._strict_parse:
            response = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=messages,
                response_format=VisualAnalysis
            )
            return response.choices[0].message.parsed

        # 2b. OpenRouter path: plain completion + tolerant JSON parse,
        # since free models inconsistently support structured outputs.
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"},
            )
        except Exception:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
            )

        content = response.choices[0].message.content
        return VisualAnalysis(**extract_json(content))
