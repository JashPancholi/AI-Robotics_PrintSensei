import os

from dotenv import load_dotenv

from .azure_image import AzureImageProvider
from .openai_image import OpenAIImageProvider
from .storage import ImageStorage


load_dotenv()


def _default_provider_name() -> str:
    """Prefer Azure when Azure endpoint config is present.

    Explicit override via IMAGE_PROVIDER=openai|azure.
    """
    explicit = os.getenv("IMAGE_PROVIDER", "").strip().lower()
    if explicit in ("azure", "openai"):
        return explicit
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        return "azure"
    return "openai"


class ImageGenerationService:


    def __init__(self, provider=None, provider_name: str | None = None):

        if provider is not None:
            self.provider = provider
        else:
            name = (provider_name or _default_provider_name()).lower()
            if name == "azure":
                self.provider = AzureImageProvider()
            else:
                self.provider = OpenAIImageProvider()

        self.storage = ImageStorage()



    def generate(
        self,
        prompt: str,
        name="diagram"
    ):


        result = self.provider.generate(
            prompt
        )


        if not result:
            return None



        if result["type"] == "base64":

            path = self.storage.save_base64(
                result["data"],
                name
            )

            return path

        if result["type"] == "url":

            path = self.storage.save_url(
                result["data"],
                name
            )

            return path


        return None
