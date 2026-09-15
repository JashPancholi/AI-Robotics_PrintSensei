import json
import os
import re

from dotenv import load_dotenv
from openai import OpenAI

from .base import AIProvider


load_dotenv()

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_TEXT_MODEL = "z-ai/glm-5.2:free"


def extract_json(content: str) -> dict:
    """Pull a JSON object out of free-model chat output.

    Handles markdown fences (```json ... ```), leading/trailing chatter,
    control characters, and truncated output (missing closing braces).
    Raises ValueError if nothing parses.
    """
    if not content or not content.strip():
        raise ValueError("Empty model output: no content to parse.")
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    # Free models often emit a stray leading brace ("{\n{...").
    # Collapse repeated opening braces so repair/parse can succeed.
    collapsed = re.sub(r"^\s*\{\s*\{\s*", "{", text)
    while collapsed != text:
        text = collapsed
        collapsed = re.sub(r"^\s*\{\s*\{\s*", "{", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Second attempt: tolerate literal control characters inside strings.
    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError:
            pass
    else:
        candidate = text[start:] if start != -1 else text
    # Last resort: repair truncated JSON by closing open braces/brackets
    # and terminating the final open string. Only used when the model
    # output was cut off (e.g. max_tokens limit).
    try:
        repaired = _repair_truncated_json(candidate)
        return json.loads(repaired, strict=False)
    except (json.JSONDecodeError, ValueError):
        pass
    raise ValueError(f"No JSON object found in model output: {content[:300]!r}")


def _repair_truncated_json(candidate: str) -> str:
    """Close an incomplete JSON object cut off mid-generation."""
    out: list[str] = []
    stack: list[str] = []
    in_string = False
    escaped = False
    for ch in candidate:
        if in_string:
            out.append(ch)
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
        elif ch in "{[":
            stack.append(ch)
            out.append(ch)
        elif ch in "}]":
            if stack:
                stack.pop()
            out.append(ch)
        else:
            out.append(ch)
    if in_string:
        out.append('"')
    while stack:
        opener = stack.pop()
        out.append("}" if opener == "{" else "]")
    return "".join(out)


def _default_headers() -> dict:
    headers = {}
    referer = os.getenv("OPENROUTER_REFERER", "https://github.com/printsensei")
    if referer:
        headers["HTTP-Referer"] = referer
    title = os.getenv("OPENROUTER_TITLE", "PrintSensei")
    if title:
        headers["X-Title"] = title
    return headers


class OpenRouterProvider(AIProvider):
    """Text/JSON provider backed by OpenRouter (OpenAI-compatible).

    Env:
    - OPENROUTER_API_KEY (required): free key from https://openrouter.ai/keys
    - OPENROUTER_TEXT_MODEL (default "z-ai/glm-5.2:free")
    - OPENROUTER_REFERER / OPENROUTER_TITLE (optional ranking headers)
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        max_tokens: int | None = None,
    ):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY is not set. "
                "Get a free key at https://openrouter.ai/keys (no card required)."
            )
        self.model = model or os.getenv("OPENROUTER_TEXT_MODEL", DEFAULT_TEXT_MODEL)
        fallbacks = os.getenv("OPENROUTER_TEXT_FALLBACKS", "")
        self.models = [self.model] + [m.strip() for m in fallbacks.split(",") if m.strip()]
        # Cap output tokens: OpenRouter reserves the full context window
        # against your credit balance unless max_tokens is set, which makes
        # even free models fail with 402 on fresh accounts.
        self.max_tokens = max_tokens or int(os.getenv("OPENROUTER_MAX_TOKENS", "2048"))
        self.client = OpenAI(
            base_url=base_url or os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
            api_key=self.api_key,
            default_headers=_default_headers(),
        )

    def _extract_message_content(self, message) -> str | None:
        if message is None:
            return None
        content = getattr(message, "content", None)
        if content and str(content).strip():
            return content
        # Reasoning models (e.g. Nemotron Ultra) sometimes put JSON in
        # reasoning fields with empty content — try those before giving up.
        for attr in ("reasoning_content", "reasoning", "reasoning_details"):
            extra = getattr(message, attr, None)
            if isinstance(extra, str) and extra.strip():
                return extra
            if isinstance(extra, list) and extra:
                texts = [str(p.get("text", "")) for p in extra if isinstance(p, dict)]
                joined = "".join(texts).strip()
                if joined:
                    return joined
        return None

    def generate_structured_output(self, prompt: str, schema: dict):
        # Free models often reject response_format, return empty choices,
        # or emit chatter around JSON — retry like VisionService does,
        # falling through to OPENROUTER_TEXT_FALLBACKS models.
        last_error: Exception | None = None
        for model in self.models:
            for _ in range(3):
                try:
                    response = self.client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": "You create structured diagram specifications. Return ONLY JSON."},
                            {"role": "user", "content": prompt},
                        ],
                        max_tokens=self.max_tokens,
                        response_format={"type": "json_object"},
                    )
                except Exception as exc:
                    message = str(exc).lower()
                    if "response_format" in message or "json" in message or "invalid" in message or "400" in message:
                        try:
                            response = self.client.chat.completions.create(
                                model=model,
                                messages=[
                                    {"role": "system", "content": "You create structured diagram specifications. Return ONLY JSON, no markdown, no commentary."},
                                    {"role": "user", "content": prompt},
                                ],
                                max_tokens=self.max_tokens,
                            )
                        except Exception as exc2:  # noqa: BLE001 - retry on provider errors
                            last_error = exc2
                            continue
                    else:
                        last_error = exc
                        continue

                try:
                    choices = getattr(response, "choices", None)
                    if not choices:
                        last_error = ValueError(f"Provider {model!r} returned no choices.")
                        continue
                    content = self._extract_message_content(choices[0].message)
                    if not content or not str(content).strip():
                        last_error = ValueError(f"Provider {model!r} returned empty content.")
                        continue
                    return extract_json(content)
                except Exception as exc:  # noqa: BLE001 - retry on parse failure
                    last_error = exc
                    continue
        raise ValueError(f"Text models {self.models!r} did not return valid JSON: {last_error}")
