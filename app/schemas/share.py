from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl

from app.enums.status import Status
from app.schemas.study import PreviewAsset


class QrShareResponse(BaseModel):
    id: UUID
    history_id: UUID
    public_url: HttpUrl
    qr_preview: PreviewAsset
    created_at: datetime
    expires_at: datetime
    print_count: int = Field(ge=0)


class QrSharePrintResponse(BaseModel):
    share_id: UUID
    status: Status
    message: str
    print_count: int = Field(ge=1)
