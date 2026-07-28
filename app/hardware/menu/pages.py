from dataclasses import dataclass
from enum import Enum


class MenuAction(str, Enum):
    STUDY = "study"
    INVENTORY = "inventory"
    QR = "qr"
    PRODUCT = "product"
    HISTORY = "history"
    SETTINGS = "settings"


@dataclass(frozen=True)
class MenuItem:
    title: str
    action: MenuAction


def main_menu_items() -> list[MenuItem]:
    return [
        MenuItem("Study Label", MenuAction.STUDY),
        MenuItem("Inventory Label", MenuAction.INVENTORY),
        MenuItem("QR Label", MenuAction.QR),
        MenuItem("Product Label", MenuAction.PRODUCT),
        MenuItem("History", MenuAction.HISTORY),
        MenuItem("Settings", MenuAction.SETTINGS),
    ]
