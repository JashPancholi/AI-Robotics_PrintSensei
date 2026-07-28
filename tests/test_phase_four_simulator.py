import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.enums.device_state import DeviceState
from app.enums.label_type import LabelType
from app.hardware.display.lcd_simulator import LCDSimulator
from app.hardware.events import Event, EventDispatcher, RobotEvent
from app.hardware.input.keyboard import KeyboardMapper
from app.hardware.menu.menu import Menu
from app.hardware.menu.pages import main_menu_items
from app.hardware.simulator import RobotSimulator
from app.renderer import LabelRenderer


def test_keyboard_mapping_returns_robot_events():
    mapper = KeyboardMapper()

    assert mapper.map_key("Up") is RobotEvent.BUTTON_UP
    assert mapper.map_key("Down") is RobotEvent.BUTTON_DOWN
    assert mapper.map_key("Return") is RobotEvent.BUTTON_OK
    assert mapper.map_key("Escape") is RobotEvent.BUTTON_BACK
    assert mapper.map_key("space") is None


def test_event_dispatcher_invokes_subscribers():
    dispatcher = EventDispatcher()
    received = []
    dispatcher.subscribe(RobotEvent.BUTTON_OK, received.append)

    dispatcher.publish(Event(RobotEvent.BUTTON_OK, {"source": "test"}))

    assert received == [Event(RobotEvent.BUTTON_OK, {"source": "test"})]


def test_menu_navigation_wraps_and_selects_items():
    menu = Menu(main_menu_items())

    menu.move_up()
    assert menu.selected_item.title == "Settings"

    menu.move_down()
    assert menu.selected_item.title == "Study Label"

    menu.move_down()
    assert menu.selected_item.title == "Inventory Label"


def test_lcd_simulator_renders_fixed_internal_resolution():
    display = LCDSimulator()

    frame = display.render_ready()

    assert isinstance(frame, Image.Image)
    assert frame.size == (320, 240)


def test_lcd_simulator_renders_all_screen_functions(tmp_path):
    display = LCDSimulator()
    preview_file = tmp_path / "preview.png"
    Image.new("RGB", (384, 180), "white").save(preview_file)

    frames = [
        display.render_boot(0.2),
        display.render_boot(0.5),
        display.render_menu(Menu(main_menu_items())),
        display.render_preview("Inventory Label", ["Arduino UNO", "Shelf B2", "Qty 12"], preview_file=preview_file),
        display.render_printing(0.1),
        display.render_printing(0.45),
        display.render_printing(0.75),
        display.render_printing(1.0),
        display.render_done(),
        display.render_error("Paper door open"),
        display.render_camera_placeholder(),
        display.render_ocr_placeholder(),
        display.render_voice_placeholder(),
        display.render_ai_placeholder(),
    ]

    assert all(frame.size == (320, 240) for frame in frames)


def test_simulator_startup_moves_from_booting_to_ready(tmp_path):
    simulator = RobotSimulator(renderer=LabelRenderer(tmp_path))

    simulator.start(interactive=False)

    assert simulator.state is DeviceState.READY
    assert simulator.display.frame.size == (320, 240)


def test_simulator_generates_inventory_preview_with_renderer(tmp_path):
    simulator = RobotSimulator(renderer=LabelRenderer(tmp_path))
    simulator.start(interactive=False)

    simulator.handle_key("Return")
    simulator.handle_key("Down")
    simulator.handle_key("Return")

    assert simulator.state is DeviceState.PREVIEW
    assert simulator.current_label is not None
    assert simulator.current_label.label_type is LabelType.INVENTORY
    assert simulator.preview_file is not None
    assert simulator.preview_file.exists()


def test_printing_simulation_returns_to_ready(tmp_path):
    simulator = RobotSimulator(renderer=LabelRenderer(tmp_path))
    simulator.start(interactive=False)

    simulator.handle_key("Return")
    simulator.handle_key("Down")
    simulator.handle_key("Return")
    simulator.handle_key("Return")

    assert simulator.state is DeviceState.READY
