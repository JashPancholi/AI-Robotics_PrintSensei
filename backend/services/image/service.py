from .openai_image import OpenAIImageProvider
from .storage import ImageStorage



class ImageGenerationService:


    def __init__(self):

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


        return None