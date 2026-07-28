from datetime import date as date_type
from typing import Any

from pydantic import BaseModel, Field

from app.enums.label_type import LabelType


class RenderRequest(BaseModel):
    title: str = Field(default="Untitled Label")
    subtitle: str | None = None
    body: str | None = None
    quantity: int | None = None
    price: float | None = None
    date: date_type | None = None
    qr_data: str | None = None
    template: str | None = None
    image_path: str | None = None
    label_type: LabelType = LabelType.INVENTORY
    shelf: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenderResponse(BaseModel):
    status: str
    file: str
    width: int
    height: int
