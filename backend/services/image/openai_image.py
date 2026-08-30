import os

from dotenv import load_dotenv
from openai import OpenAI

from .base import ImageProvider


load_dotenv()


class OpenAIImageProvider(ImageProvider):

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv(
                "OPENAI_API_KEY"
            )
        )


    def generate(
        self,
        prompt: str
    ):

        response = self.client.images.generate(

            model="gpt-image-2",

            prompt=prompt,

            size="1024x1024",

            quality="medium"

        )


        image = response.data[0]


        if image.url:

            return {
                "type": "url",
                "data": image.url
            }


        if image.b64_json:

            return {
                "type": "base64",
                "data": image.b64_json
            }


        return None
    