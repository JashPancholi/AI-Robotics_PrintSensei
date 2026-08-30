import base64
import json
from pathlib import Path

from openai import OpenAI
from dotenv import load_dotenv

from .models import VisualAnalysis


load_dotenv()


class VisionService:


    def __init__(self):

        self.client = OpenAI()



    def analyze(
        self,
        image_path: str
    ) -> VisualAnalysis:


        image_file = Path(image_path)


        with open(
            image_file,
            "rb"
        ) as file:

            image_data = base64.b64encode(
                file.read()
            ).decode("utf-8")


        response = self.client.chat.completions.create(

            model="gpt-4.1-mini",

            messages=[

                {
                    "role": "system",

                    "content":
                    """
                    Analyze the uploaded image.

                    Return JSON containing:

                    - description
                    - detected_objects
                    - extracted_text
                    - image_type
                    - important_details

                    extracted_text must be an array.

                    important_details must be an array.
                    """
                },


                {
                    "role": "user",

                    "content":[

                        {
                            "type":"text",
                            "text":
                            "Analyze this image"
                        },


                        {
                            "type":"image_url",

                            "image_url":{
                                "url":
                                f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }

            ],

            response_format={
                "type":"json_object"
            }
        )


        # GPT response is a JSON string
        result = (
            response
            .choices[0]
            .message
            .content
        )


        # Convert JSON string → Python dictionary
        data = json.loads(
            result
        )


        # Fix extracted_text if GPT returns string
        if isinstance(
            data.get("extracted_text"),
            str
        ):

            data["extracted_text"] = [
                data["extracted_text"]
            ]


        # Fix important_details if GPT returns dictionary
        if isinstance(
            data.get("important_details"),
            dict
        ):

            data["important_details"] = [
                f"{key}: {value}"
                for key, value
                in data["important_details"].items()
            ]


        # Pydantic validates final structure here
        return VisualAnalysis(
            **data
        )