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
    and truncated whitespace. Raises ValueError if nothing parses.
    """
    text = content.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(text[start : end + 1])
    raise ValueError(f"No JSON object found in model output: {content[:300]!r}")


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
        # Cap output tokens: OpenRouter reserves the full context window
        # against your credit balance unless max_tokens is set, which makes
        # even free models fail with 402 on fresh accounts.
        self.max_tokens = max_tokens or int(os.getenv("OPENROUTER_MAX_TOKENS", "2048"))
        self.client = OpenAI(
            base_url=base_url or os.getenv("OPENROUTER_BASE_URL", OPENROUTER_BASE_URL),
            api_key=self.api_key,
            default_headers=_default_headers(),
        )

    def generate_structured_output(self, prompt: str, schema: dict):
        # Free models often reject response_format, so try strict first,
        # fall back to plain completion + tolerant extraction.
        try:
            response = self.client.chat.completions.create(
                model=self.model,
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
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You create structured diagram specifications. Return ONLY JSON, no markdown, no commentary."},
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=self.max_tokens,
                )
            else:
                raise

        content = response.choices[0].message.content
        return extract_json(content)
