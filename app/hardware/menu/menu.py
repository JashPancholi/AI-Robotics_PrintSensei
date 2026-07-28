import logging

from app.hardware.menu.pages import MenuItem

logger = logging.getLogger(__name__)


class Menu:
    """Navigable menu model independent from display and keyboard."""

    def __init__(self, items: list[MenuItem]) -> None:
        if not items:
            raise ValueError("Menu requires at least one item")
        self.items = items
        self.selected_index = 0

    @property
    def selected_item(self) -> MenuItem:
        return self.items[self.selected_index]

    def move_up(self) -> MenuItem:
        self.selected_index = (self.selected_index - 1) % len(self.items)
        logger.info("Menu changed: %s", self.selected_item.title)
        return self.selected_item

    def move_down(self) -> MenuItem:
        self.selected_index = (self.selected_index + 1) % len(self.items)
        logger.info("Menu changed: %s", self.selected_item.title)
        return self.selected_item

    def visible_items(self, count: int = 4) -> list[tuple[int, MenuItem]]:
        start = max(0, min(self.selected_index, len(self.items) - count))
        return list(enumerate(self.items[start : start + count], start=start))
