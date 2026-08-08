from pydantic import BaseModel
from typing import Any


class Response(BaseModel):

    success: bool

    message: str

    payload: Any = None