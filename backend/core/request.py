from pathlib import Path
from typing import Optional

from pydantic import BaseModel

from .enums import TaskType


class Request(BaseModel):

    task: TaskType

    instruction: str

    image: Optional[Path] = None

    input_mode: str = "text"

    detail_level: str = "medium"