from enum import Enum


class EventName(str, Enum):
    BUTTON_OK = "button_ok"
    VOICE_RECEIVED = "voice_received"
    CAMERA_CAPTURED = "camera_captured"
    OCR_DONE = "ocr_done"
    LABEL_READY = "label_ready"
    PRINT_COMPLETE = "print_complete"
    ERROR_OCCURRED = "error_occurred"
