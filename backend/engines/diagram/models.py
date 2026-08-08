from pydantic import BaseModel, Field


class DiagramElement(BaseModel):
    name: str
    description: str


class DiagramSpecification(BaseModel):
    title: str
    style: str = "educational"
    orientation: str = "portrait"
    labels: bool = True

    elements: list[DiagramElement] = Field(default_factory=list)