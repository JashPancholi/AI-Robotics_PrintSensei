from enum import Enum


class Intent(str, Enum):
    STUDY = "study"
    INVENTORY = "inventory"
    PRODUCT = "product"
    QR = "qr"
    OCR = "ocr"
    UNKNOWN = "unknown"
