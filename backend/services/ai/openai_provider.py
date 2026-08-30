import os
import json

from dotenv import load_dotenv
from openai import OpenAI

from .base import AIProvider


load_dotenv()


class OpenAIProvider(AIProvider):

    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv(
                "OPENAI_API_KEY"
            )
        )


    def generate_structured_output(
        self,
        prompt: str,
        schema: dict
    ):

        response = self.client.chat.completions.create(

            model="gpt-4.1-mini",

            messages=[

                {
                    "role": "system",
                    "content":
                    "You return valid JSON matching the structure requested by the user."
                },

                {
                    "role": "user",
                    "content": prompt
                }
            ],

            response_format={
                "type": "json_object"
            }
        )


        content = response.choices[0].message.content


        return json.loads(content)
