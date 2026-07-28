from datetime import date as date_type
from typing import Any

from pydantic import BaseModel, Field

from app.enums.label_type import LabelType


class LabelData(BaseModel):
    title: str
    subtitle: str | None = None
    body: str | None = None
    quantity: int | None = None
    price: float | None = None
    date: date_type | None = None
    qr_data: str | None = None
    template: str | None = None
    image_path: str | None = None
    label_type: LabelType = LabelType.CUSTOM
    metadata: dict[str, Any] = Field(default_factory=dict)
