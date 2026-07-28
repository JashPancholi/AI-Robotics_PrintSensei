from enum import Enum


class InputType(str, Enum):
    VOICE = "voice"
    TEXT = "text"
    CAMERA = "camera"
    OCR = "ocr"
    MANUAL = "manual"
