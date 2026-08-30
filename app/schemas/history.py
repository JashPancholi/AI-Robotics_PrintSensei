from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.enums.status import Status
from app.schemas.study import PreviewAsset


class HistoryItemResponse(BaseModel):
    id: UUID
    prompt: str
    title: str
    content_type: Literal["notes", "diagram"]
    preview: PreviewAsset
    created_at: datetime
    last_printed_at: datetime | None = None
    print_count: int = Field(ge=0)


class HistoryListResponse(BaseModel):
    items: list[HistoryItemResponse]


class HistoryPrintResponse(BaseModel):
    request_id: UUID
    status: Status
    message: str
    print_count: int = Field(ge=1)
