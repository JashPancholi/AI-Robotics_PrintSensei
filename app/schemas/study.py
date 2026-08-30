from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.enums.label_type import LabelType
from app.enums.status import Status


class StudyGenerateRequest(BaseModel):
    text: str = Field(
        min_length=1,
        max_length=2_000,
        description="The text instruction used to create the study label.",
        examples=["Explain binary search in four concise points."],
    )
    detail_level: Literal["low", "medium", "high"] = Field(
        default="medium",
        description="Controls how much study content is generated.",
    )

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("text must not be blank")
        return normalized


class StudyLabelPayload(BaseModel):
    title: str
    points: list[str] = Field(min_length=1)
    content_type: Literal["notes", "diagram"]
    label_type: Literal[LabelType.STUDY] = LabelType.STUDY


class PreviewAsset(BaseModel):
    url: str = Field(description="Browser-accessible URL for the rendered label image.")
    width: int = Field(gt=0)
    height: int = Field(gt=0)


class StudyGenerateResponse(BaseModel):
    request_id: UUID
    status: Status
    label: StudyLabelPayload
    preview: PreviewAsset


class StudyJobStartResponse(BaseModel):
    request_id: UUID
    status: Status
    progress: int = Field(ge=0, le=100)
    stage: str


class StudyJobStatusResponse(StudyJobStartResponse):
    result: StudyGenerateResponse | None = None
    error: str | None = None


class StudyPrintResponse(BaseModel):
    request_id: UUID
    status: Status
    message: str
