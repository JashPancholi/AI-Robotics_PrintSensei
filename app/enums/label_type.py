from enum import Enum


class LabelType(str, Enum):
    STUDY = "study"
    INVENTORY = "inventory"
    PRODUCT = "product"
    QR = "qr"
    WARNING = "warning"
    CUSTOM = "custom"
