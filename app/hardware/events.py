import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class RobotEvent(str, Enum):
    BUTTON_UP = "button_up"
    BUTTON_DOWN = "button_down"
    BUTTON_OK = "button_ok"
    BUTTON_BACK = "button_back"
    START_PRINT = "start_print"
    PREVIEW_READY = "preview_ready"
    PRINT_COMPLETE = "print_complete"
    ERROR = "error"
    STATE_CHANGED = "state_changed"


@dataclass(frozen=True)
class Event:
    name: RobotEvent
    payload: dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[Event], None]


class EventDispatcher:
    """Small publish/subscribe dispatcher for simulator and hardware events."""

    def __init__(self) -> None:
        self._subscribers: dict[RobotEvent, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: RobotEvent, handler: EventHandler) -> None:
        self._subscribers[event_name].append(handler)

    def publish(self, event: Event) -> None:
        logger.info("Event published: %s", event.name.value)
        for handler in self._subscribers[event.name]:
            handler(event)
