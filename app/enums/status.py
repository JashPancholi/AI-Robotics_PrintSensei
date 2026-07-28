from enum import Enum


class Status(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    READY = "ready"
    PRINTING = "printing"
    DONE = "done"
    ERROR = "error"
