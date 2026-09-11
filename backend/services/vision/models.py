from typing import List, Optional
from pydantic import BaseModel, Field


class VisionElement(BaseModel):
    name: str = Field(description="Name or title of the detected component/object.")
    description: Optional[str] = Field(default=None, description="Brief explanation of the component.")
    position: Optional[str] = Field(
        default=None, 
        description="Spatial position in the image (e.g., 'center', 'top-left', 'inner core')."
    )


class VisionRelationship(BaseModel):
    source: str = Field(description="Source element name.")
    target: str = Field(description="Target element name.")
    description: str = Field(description="How the two components connect, interact, or relate.")


class VisualAnalysis(BaseModel):
    image_type: Optional[str] = Field(
        default="unknown", 
        description="Classification (e.g., technical_diagram, handwriting, schematic, object_photo)."
    )
    description: str = Field(description="High-level description of what the image portrays.")
    extracted_text: List[str] = Field(
        default_factory=list, 
        description="All OCR labels and textual content visible in the image."
    )
    elements: List[VisionElement] = Field(
        default_factory=list, 
        description="List of distinct structural parts or objects identified."
    )
    relationships: List[VisionRelationship] = Field(
        default_factory=list, 
        description="Visual or functional connections between identified elements."
    )
    important_details: List[str] = Field(
        default_factory=list, 
        description="Visual layout traits (e.g., high-contrast lines, flow arrows)."
    )