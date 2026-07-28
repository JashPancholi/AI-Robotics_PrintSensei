import logging

from app.hardware.events import Event, EventDispatcher, RobotEvent

logger = logging.getLogger(__name__)


class KeyboardMapper:
    """Maps PC keyboard keys into robot button events."""

    _mapping = {
        "Up": RobotEvent.BUTTON_UP,
        "Down": RobotEvent.BUTTON_DOWN,
        "Return": RobotEvent.BUTTON_OK,
        "Escape": RobotEvent.BUTTON_BACK,
    }

    def __init__(self, dispatcher: EventDispatcher | None = None) -> None:
        self.dispatcher = dispatcher

    def map_key(self, key: str) -> RobotEvent | None:
        return self._mapping.get(key)

    def handle_key(self, key: str) -> RobotEvent | None:
        event_name = self.map_key(key)
        if event_name is None:
            return None

        logger.info("Keyboard %s", key)
        if self.dispatcher is not None:
            self.dispatcher.publish(Event(event_name))
        return event_name
