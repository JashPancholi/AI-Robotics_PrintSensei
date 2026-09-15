import os

from dotenv import load_dotenv
from openai import OpenAI

from .base import AIProvider
from .openrouter_provider import _default_headers, extract_json


load_dotenv()

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_MODEL = "meta/muse-glimmer-30b"


class NvidiaProvider(AIProvider):
    """Text/JSON provider backed by NVIDIA NIM (OpenAI-compatible).

    Env:
    - NVIDIA_API_KEY (required): key from https://build.nvidia.com
    - NVIDIA_TEXT_MODEL (default "meta/muse-glimmer-30b")
    - NVIDIA_MAX_TOKENS (default "2048")
    - NVIDIA_BASE_URL (default "https://integrate.api.nvidia.com/v1")
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        max_tokens: int | None = None,
    ):
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not self.api_key:
            raise ValueError(
                "NVIDIA_API_KEY is not set. "
                "Get one at https://build.nvidia.com (Sign In -> API Keys)."
            )
        self.model = model or os.getenv("NVIDIA_TEXT_MODEL", DEFAULT_NVIDIA_MODEL)
        self.max_tokens = max_tokens or int(os.getenv("NVIDIA_MAX_TOKENS", "2048"))
        self.client = OpenAI(
            base_url=base_url or os.getenv("NVIDIA_BASE_URL", NVIDIA_BASE_URL),
            api_key=self.api_key,
            default_headers=_default_headers(),
        )

    def _extract_message_content(self, message) -> str | None:
        if message is None:
            return None
        content = getattr(message, "content", None)
        if content and str(content).strip():
            return content
        for attr in ("reasoning_content", "reasoning", "reasoning_details"):
            extra = getattr(message, attr, None)
            if isinstance(extra, str) and extra.strip():
                return extra
        return None

    def generate_structured_output(self, prompt: str, schema: dict):
        last_error: Exception | None = None
        for _ in range(3):
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
                    try:
                        response = self.client.chat.completions.create(
                            model=self.model,
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
                    last_error = ValueError(f"Provider {self.model!r} returned no choices.")
                    continue
                content = self._extract_message_content(choices[0].message)
                if not content or not str(content).strip():
                    last_error = ValueError(f"Provider {self.model!r} returned empty content.")
                    continue
                return extract_json(content)
            except Exception as exc:  # noqa: BLE001 - retry on parse failure
                last_error = exc
                continue
        raise ValueError(f"NVIDIA model {self.model!r} did not return valid JSON: {last_error}")
