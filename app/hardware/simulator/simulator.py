import logging
from pathlib import Path

from app.enums.device_state import DeviceState
from app.enums.label_type import LabelType
from app.hardware.display.lcd_simulator import LCDSimulator
from app.hardware.events import Event, EventDispatcher, RobotEvent
from app.hardware.input.keyboard import KeyboardMapper
from app.hardware.menu.menu import Menu
from app.hardware.menu.pages import MenuAction, main_menu_items
from app.models.label_data import LabelData
from app.renderer import LabelRenderer, RenderResult
from app.state.state_machine import StateMachine

logger = logging.getLogger(__name__)


class RobotSimulator:
    """Coordinates PC robot simulation without embedding display business logic."""

    def __init__(
        self,
        display: LCDSimulator | None = None,
        dispatcher: EventDispatcher | None = None,
        renderer: LabelRenderer | None = None,
    ) -> None:
        self.display = display or LCDSimulator()
        self.dispatcher = dispatcher or EventDispatcher()
        self.renderer = renderer or LabelRenderer()
        self.keyboard = KeyboardMapper(self.dispatcher)
        self.state_machine = StateMachine(DeviceState.BOOTING)
        self.menu = Menu(main_menu_items())
        self.current_label: LabelData | None = None
        self.preview_file: Path | None = None
        self.confirm_index = 0
        self._subscribe_events()

    @property
    def state(self) -> DeviceState:
        return self.state_machine.current_state

    def start(self, interactive: bool = True) -> None:
        logger.info("Simulator startup")
        if interactive:
            self.display.open_window(self.keyboard.handle_key)
            self._run_boot_sequence()
        else:
            self.display.show(self.display.render_boot(1.0))
            self._finish_boot()
        if interactive:
            self.display.run()

    def handle_key(self, key: str) -> None:
        self.keyboard.handle_key(key)

    def _finish_boot(self) -> None:
        self.display.show(self.display.render_boot(1.0))
        self._set_state(DeviceState.READY)
        self.display.show(self.display.render_ready())

    def _run_boot_sequence(self) -> None:
        steps = [
            (0, 0.1),
            (650, 0.4),
            (1300, 0.7),
            (1950, 1.0),
        ]
        for delay_ms, progress in steps:
            self.display.after(delay_ms, lambda value=progress: self.display.show(self.display.render_boot(value)))
        self.display.after(2400, self._finish_boot)

    def _subscribe_events(self) -> None:
        self.dispatcher.subscribe(RobotEvent.BUTTON_UP, self._on_up)
        self.dispatcher.subscribe(RobotEvent.BUTTON_DOWN, self._on_down)
        self.dispatcher.subscribe(RobotEvent.BUTTON_OK, self._on_ok)
        self.dispatcher.subscribe(RobotEvent.BUTTON_BACK, self._on_back)
        self.dispatcher.subscribe(RobotEvent.START_PRINT, self._on_start_print)
        self.dispatcher.subscribe(RobotEvent.PRINT_COMPLETE, self._on_print_complete)
        self.dispatcher.subscribe(RobotEvent.ERROR, self._on_error)

    def _on_up(self, event: Event) -> None:
        if self.state is DeviceState.MENU:
            self.menu.move_up()
            self.display.show(self.display.render_menu(self.menu))
        elif self.state is DeviceState.PREVIEW:
            self.confirm_index = (self.confirm_index - 1) % 2
            self._show_preview()

    def _on_down(self, event: Event) -> None:
        if self.state is DeviceState.MENU:
            self.menu.move_down()
            self.display.show(self.display.render_menu(self.menu))
        elif self.state is DeviceState.PREVIEW:
            self.confirm_index = (self.confirm_index + 1) % 2
            self._show_preview()

    def _on_ok(self, event: Event) -> None:
        if self.state is DeviceState.READY:
            self._set_state(DeviceState.MENU)
            self.display.show(self.display.render_menu(self.menu))
        elif self.state is DeviceState.MENU:
            self._generate_preview(self.menu.selected_item.action)
        elif self.state is DeviceState.PREVIEW:
            if self.confirm_index == 0:
                self.dispatcher.publish(Event(RobotEvent.START_PRINT))
            else:
                self._return_ready()

    def _on_back(self, event: Event) -> None:
        if self.state in {DeviceState.MENU, DeviceState.PREVIEW}:
            self._return_ready()

    def _generate_preview(self, action: MenuAction) -> None:
        if self.state is DeviceState.MENU:
            self._set_state(DeviceState.LISTENING)
        self._set_state(DeviceState.PROCESSING)
        self.display.show(self.display.render_boot(0.5))
        self.current_label = self._sample_label(action)
        logger.info("Renderer called")
        result = self.renderer.render(self.current_label)
        self.preview_file = Path(result.file)
        logger.info("Preview generated: %s", result.file)
        self.dispatcher.publish(Event(RobotEvent.PREVIEW_READY, {"file": result.file}))
        self._set_state(DeviceState.PREVIEW)
        self.confirm_index = 0
        self._show_preview()

    def _on_start_print(self, event: Event) -> None:
        logger.info("Printing started")
        self._set_state(DeviceState.PRINTING)
        for delay_ms, progress in [(0, 0.15), (600, 0.45), (1200, 0.75), (1800, 1.0)]:
            self.display.after(delay_ms, lambda value=progress: self.display.show(self.display.render_printing(value)))
        self.display.after(2200, lambda: self.dispatcher.publish(Event(RobotEvent.PRINT_COMPLETE)))

    def _on_print_complete(self, event: Event) -> None:
        logger.info("Printing finished")
        self._set_state(DeviceState.DONE)
        self.display.show(self.display.render_done())
        self.display.after(2000, self._return_ready)

    def _on_error(self, event: Event) -> None:
        self._set_state(DeviceState.ERROR)
        self.display.show(self.display.render_error(str(event.payload.get("message", "ERROR"))))

    def _return_ready(self) -> None:
        if self.state is DeviceState.DONE:
            self.state_machine.transition_to(DeviceState.READY)
        elif self.state is DeviceState.ERROR:
            self.state_machine.transition_to(DeviceState.READY)
        elif self.state is DeviceState.MENU:
            self.state_machine.transition_to(DeviceState.READY)
        elif self.state is DeviceState.PREVIEW:
            self.state_machine.transition_to(DeviceState.READY)
        self.dispatcher.publish(Event(RobotEvent.STATE_CHANGED, {"state": self.state.value}))
        self.display.show(self.display.render_ready())

    def _set_state(self, state: DeviceState) -> None:
        if self.state != state:
            self.state_machine.transition_to(state)
        self.dispatcher.publish(Event(RobotEvent.STATE_CHANGED, {"state": state.value}))

    def _show_preview(self) -> None:
        if self.current_label is None:
            return
        self.display.show(
            self.display.render_preview(
                self._preview_title(),
                self._preview_details(),
                self.confirm_index,
                self.preview_file,
            )
        )

    def _preview_title(self) -> str:
        if self.current_label is None:
            return "Label"
        return f"{self.current_label.label_type.value.title()} Label"

    def _preview_details(self) -> list[str]:
        label = self.current_label
        if label is None:
            return []
        details = [label.title]
        shelf = label.metadata.get("shelf")
        if shelf:
            details.append(f"Shelf {shelf}")
        if label.quantity is not None:
            details.append(f"Qty {label.quantity}")
        if label.price is not None:
            details.append(f"Price Rs {label.price:g}")
        if label.qr_data and label.label_type is LabelType.QR:
            details.append(label.qr_data)
        return details

    def _sample_label(self, action: MenuAction) -> LabelData:
        if action is MenuAction.INVENTORY:
            return LabelData(
                title="Arduino UNO",
                quantity=12,
                qr_data="inventory:arduino-uno",
                label_type=LabelType.INVENTORY,
                metadata={"shelf": "B2"},
            )
        if action is MenuAction.STUDY:
            return LabelData(
                title="Binary Search",
                body="Sorted array\nO(log n)\nDivide and conquer",
                qr_data="https://example.com/study/binary-search",
                label_type=LabelType.STUDY,
            )
        if action is MenuAction.QR:
            return LabelData(
                title="Scan Me",
                qr_data="https://github.com",
                label_type=LabelType.QR,
            )
        if action is MenuAction.PRODUCT:
            return LabelData(title="Coffee", price=250, label_type=LabelType.PRODUCT)
        return LabelData(title=action.value.title(), label_type=LabelType.CUSTOM)
