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

DEFAULT_VISION_MODEL = "inclusionai/ling-3.0-flash-vl:free"

_SYSTEM_PROMPT = (
    "You are an expert visual perception model for PrintSensei. "
    "Analyze the image and extract OCR text, visual components, "
    "their spatial arrangements, and relationships. Return ONLY JSON "
    "with exactly these keys: image_type (string), description (string, required), "
    "extracted_text (array of strings), elements (array of {name, description, position}), "
    "relationships (array of {source, target, description}), "
    "important_details (array of strings)."
)


def _normalize_visual_data(data: object) -> dict:
    """Coerce flaky free-model JSON into VisualAnalysis shape."""
    if not isinstance(data, dict):
        raise ValueError(f"Vision JSON must be an object, got: {data!r}"[:300])
    # Model sometimes returns a single OCR element instead of full object.
    if "description" not in data and "image_type" not in data and "elements" not in data:
        text = data.get("text") or data.get("label") or data.get("name") or str(data)[:200]
        return {
            "image_type": "object_photo",
            "description": str(text),
            "extracted_text": [str(text)],
            "elements": [{"name": str(text)}],
            "relationships": [],
            "important_details": [],
        }
    out = dict(data)
    out.setdefault("image_type", "unknown")
    out.setdefault("description", out.get("image_type") or "Visual analysis")
    out.setdefault("extracted_text", [])
    out.setdefault("elements", [])
    out.setdefault("relationships", [])
    out.setdefault("important_details", [])
    # extracted_text items must be strings: {"text": "HDMI"} -> "HDMI"
    norm_text: list[str] = []
    for item in out["extracted_text"] or []:
        if isinstance(item, str):
            norm_text.append(item)
        elif isinstance(item, dict):
            for key in ("text", "label", "value", "name", "content"):
                if item.get(key):
                    norm_text.append(str(item[key]))
                    break
            else:
                norm_text.append(str(item)[:200])
        else:
            norm_text.append(str(item))
    out["extracted_text"] = norm_text
    # elements items must be {name,...}: "HDMI" -> {"name": "HDMI"}
    norm_elements: list[dict] = []
    for item in out["elements"] or []:
        if isinstance(item, str):
            norm_elements.append({"name": item})
        elif isinstance(item, dict):
            el = dict(item)
            el.setdefault("name", el.get("text") or el.get("label") or "component")
            norm_elements.append(el)
        else:
            norm_elements.append({"name": str(item)})
    out["elements"] = norm_elements
    return out


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
                    {"type": "text", "text": 'Return ONLY this JSON shape: {"image_type": "...", "description": "...", "extracted_text": ["..."], "elements": [{"name": "...", "description": "...", "position": "..."}], "relationships": [{"source": "...", "target": "...", "description": "..."}], "important_details": ["..."]}. Extract all structural details from this image.'},
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
        # Free vision models are flaky (empty replies, chatter around the
        # JSON, truncation), so retry a few times before giving up.
        last_error: Exception | None = None
        for _ in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"},
                )
            except Exception:
                try:
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=self.max_tokens,
                    )
                except Exception as exc:  # noqa: BLE001 - retry on provider errors
                    last_error = exc
                    continue

            try:
                choices = getattr(response, "choices", None)
                if not choices:
                    last_error = ValueError(f"Provider {self.model!r} returned no choices.")
                    continue
                content = choices[0].message.content if choices[0].message else None
            except Exception as exc:  # noqa: BLE001 - retry when SDK shape is unexpected
                last_error = exc
                continue
            try:
                return VisualAnalysis(**_normalize_visual_data(extract_json(content or "")))
            except Exception as exc:  # noqa: BLE001 - retry on any parse failure
                last_error = exc
        raise ValueError(
            f"Vision model {self.model!r} did not return valid JSON "
            f"after 3 attempts: {last_error}"
        )
