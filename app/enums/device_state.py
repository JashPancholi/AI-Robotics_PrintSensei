from enum import Enum


class DeviceState(str, Enum):
    BOOTING = "booting"
    READY = "ready"
    MENU = "menu"
    LISTENING = "listening"
    PROCESSING = "processing"
    PREVIEW = "preview"
    PRINTING = "printing"
    DONE = "done"
    ERROR = "error"
