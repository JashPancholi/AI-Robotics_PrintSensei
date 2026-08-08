from enum import Enum


class TaskType(str, Enum):
    NOTES = "notes"
    DIAGRAM = "diagram"
    LABEL = "label"
    QR = "qr"
    TEXT = "text"