from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from app.enums.input_type import InputType
from app.enums.intent import Intent
from app.enums.status import Status


class PrintRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    raw_input: str
    input_type: InputType
    intent: Intent = Intent.UNKNOWN
    status: Status = Status.RECEIVED
    metadata: dict[str, Any] = Field(default_factory=dict)
