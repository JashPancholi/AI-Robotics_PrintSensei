import base64
from pathlib import Path
from typing import Union
from openai import OpenAI
from dotenv import load_dotenv

from .models import VisualAnalysis

load_dotenv()


class VisionService:
    def __init__(self, client: OpenAI = None):
        self.client = client or OpenAI()

    def analyze(self, image_input: Union[str, Path]) -> VisualAnalysis:
        # 1. Handle file path or raw base64 string
        if isinstance(image_input, (str, Path)) and Path(image_input).is_file():
            with open(image_input, "rb") as file:
                image_data = base64.b64encode(file.read()).decode("utf-8")
        else:
            image_data = str(image_input)

        # 2. Call OpenAI Structured Outputs
        response = self.client.beta.chat.completions.parse(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert visual perception model for PrintSensei. "
                        "Analyze the image and extract OCR text, visual components, "
                        "their spatial arrangements, and relationships."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Extract all structural details from this image."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            response_format=VisualAnalysis
        )

        return response.choices[0].message.parsed