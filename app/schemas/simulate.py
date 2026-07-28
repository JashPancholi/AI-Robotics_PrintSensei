from pydantic import BaseModel, Field

from app.enums.intent import Intent
from app.enums.label_type import LabelType
from app.enums.status import Status


class SimulateRequest(BaseModel):
    text: str = Field(min_length=1)


class SimulateResponse(BaseModel):
    request_id: str
    intent: Intent
    status: Status
    label_type: LabelType
