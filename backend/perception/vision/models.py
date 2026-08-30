from typing import List

from pydantic import BaseModel


class VisualAnalysis(BaseModel):

    description: str

    detected_objects: List[str] = []

    extracted_text: List[str] = []

    image_type: str | None = None

    important_details: List[str] = []