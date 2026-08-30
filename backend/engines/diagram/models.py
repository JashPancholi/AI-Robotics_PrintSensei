from pydantic import BaseModel, Field
from typing import List, Optional


class DiagramElement(BaseModel):

    name: str

    description: str

    position: Optional[str] = None

    label: bool = True

    importance: int = 5


class DiagramRelationship(BaseModel):

    source: str

    target: str

    description: str


class DiagramSpecification(BaseModel):

    title: str

    description: str

    style: str = "educational"

    orientation: str = "portrait"

    labels: bool = True

    elements: List[DiagramElement] = Field(
        default_factory=list
    )

    relationships: List[DiagramRelationship] = Field(
        default_factory=list
    )

    rendering_notes: Optional[str] = None