import os

from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

from .base import ImageProvider


load_dotenv()

_FOUNDRY_SCOPE = "https://ai.azure.com/.default"
_AZURE_OPENAI_SCOPE = "https://cognitiveservices.azure.com/.default"


def _is_foundry_endpoint(endpoint: str) -> bool:
    lowered = endpoint.lower()
    return "services.ai.azure.com" in lowered or lowered.rstrip("/").endswith("/openai/v1")


def _resolve_api_key(endpoint: str, explicit: str | None = None):
    """Return an API key string or an Entra token provider callable.

    Priority: explicit arg > AZURE_OPENAI_API_KEY env > Entra ID
    (via azure-identity DefaultAzureCredential).
    """
    if explicit:
        return explicit
    env_key = os.getenv("AZURE_OPENAI_API_KEY")
    if env_key:
        return env_key
    if os.getenv("AZURE_AUTH", "").strip().lower() in ("entra", "azure_ad", "aad"):
        pass  # fall through to Entra below
    elif env_key is None and os.getenv("AZURE_OPENAI_API_KEY", None) is None:
        pass  # no key configured -> try Entra
    else:
        return env_key

    try:
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider
    except ImportError as exc:
        raise ValueError(
            "No AZURE_OPENAI_API_KEY set and azure-identity is not installed. "
            "Either set AZURE_OPENAI_API_KEY or `pip install azure-identity` "
            "and sign in with `az login` for Entra ID auth."
        ) from exc

    scope = os.getenv("AZURE_TOKEN_SCOPE") or (
        _FOUNDRY_SCOPE if _is_foundry_endpoint(endpoint) else _AZURE_OPENAI_SCOPE
    )
    return get_bearer_token_provider(DefaultAzureCredential(), scope)


class AzureImageProvider(ImageProvider):
    """Image provider backed by Azure AI Foundry / Azure OpenAI.

    Supports both auth styles:

    1. API key (Azure OpenAI resource or Foundry project):
       AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY
    2. Entra ID (your sample code style, no key needed):
       AZURE_OPENAI_ENDPOINT=https://<resource>.services.ai.azure.com/openai/v1
       + `pip install azure-identity` + `az login`.
       Uses DefaultAzureCredential with scope https://ai.azure.com/.default.

    Configuration via environment variables:

    - AZURE_OPENAI_ENDPOINT: e.g.
      https://<resource>.services.ai.azure.com/openai/v1  (Foundry, as in your sample)
      or https://<resource>.openai.azure.com/  (classic Azure OpenAI)
    - AZURE_OPENAI_API_KEY: API key. Omit to use Entra ID instead.
    - AZURE_AUTH: set to "entra" to force Entra ID even if a key exists.
    - AZURE_TOKEN_SCOPE: override token scope (default picks per endpoint).
    - AZURE_OPENAI_API_VERSION: only for classic Azure OpenAI endpoints,
      default "2024-12-01-preview".
    - AZURE_OPENAI_IMAGE_DEPLOYMENT: deployment name of the image model
      (e.g. "gpt-image-2.5-flare", "gpt-image-1", "dall-e-3"). Required.
    - AZURE_OPENAI_IMAGE_SIZE: default "1024x1024"
    - AZURE_OPENAI_IMAGE_QUALITY: optional, e.g. "low" | "medium" | "high".
      Leave unset if your deployment rejects it (gpt-image-2.5-flare does).
    - AZURE_OPENAI_IMAGE_STYLE: optional, only for dall-e-3 ("vivid" | "natural").

    The provider returns the same dict shape as OpenAIImageProvider:
    {"type": "base64", "data": ...} or {"type": "url", "data": ...}.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_key=None,
        api_version: str | None = None,
        deployment: str | None = None,
        size: str | None = None,
        quality: str | None = None,
        style: str | None = None,
    ):
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_IMAGE_DEPLOYMENT")
        self.size = size or os.getenv("AZURE_OPENAI_IMAGE_SIZE", "1024x1024")
        # Default to unset: many Foundry image deployments reject `quality`.
        self.quality = quality or os.getenv("AZURE_OPENAI_IMAGE_QUALITY") or None
        self.style = style or os.getenv("AZURE_OPENAI_IMAGE_STYLE")

        if not self.endpoint:
            raise ValueError(
                "AZURE_OPENAI_ENDPOINT is not set. "
                "Set it to your Azure endpoint, e.g. "
                "https://<resource>.services.ai.azure.com/openai/v1"
            )
        if not self.deployment:
            raise ValueError(
                "AZURE_OPENAI_IMAGE_DEPLOYMENT is not set. "
                "Set it to your image model deployment name "
                '(e.g. "gpt-image-2.5-flare").'
            )

        resolved_key = _resolve_api_key(self.endpoint, api_key)

        if _is_foundry_endpoint(self.endpoint):
            # Foundry style (your sample code): plain OpenAI client
            # pointed at the /openai/v1 base URL.
            self.client = OpenAI(
                base_url=self.endpoint,
                api_key=resolved_key,
            )
        else:
            self.api_version = (
                api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
            )
            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=resolved_key,
                api_version=self.api_version,
            )

    def generate(self, prompt: str):
        kwargs: dict = {
            "model": self.deployment,
            "prompt": prompt,
            "size": self.size,
            "n": 1,
        }

        # Quality vocab differs per model; many Foundry deployments
        # reject it entirely. Send only if configured, retry without it.
        if self.quality:
            kwargs["quality"] = self.quality

        # Style is dall-e-3 only.
        if self.style:
            kwargs["style"] = self.style

        try:
            response = self.client.images.generate(**kwargs)
        except Exception as exc:
            message = str(exc).lower()
            if self.quality and ("quality" in message or "invalid" in message):
                kwargs.pop("quality", None)
                response = self.client.images.generate(**kwargs)
            else:
                raise

        image = response.data[0]

        if getattr(image, "b64_json", None):
            return {"type": "base64", "data": image.b64_json}

        if getattr(image, "url", None):
            result: dict = {"type": "url", "data": image.url}
            revised = getattr(image, "revised_prompt", None)
            if revised:
                result["revised_prompt"] = revised
            return result

        return None
