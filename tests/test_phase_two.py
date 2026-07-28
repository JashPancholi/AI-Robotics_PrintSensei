import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.fake_request_generator import create_fake_print_request
from app.enums.device_state import DeviceState
from app.enums.intent import Intent
from app.enums.label_type import LabelType
from app.enums.status import Status
from app.main import app
from app.state.state_machine import StateMachine

client = TestClient(app)


def test_simulate_inventory_request_returns_phase_two_completion_payload():
    response = client.post(
        "/simulate",
        json={"text": "Create inventory label for Arduino Uno"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["request_id"]
    assert body["intent"] == "inventory"
    assert body["status"] == "processing"
    assert body["label_type"] == "inventory"


def test_fake_request_generator_detects_qr_requests():
    print_request, label_data = create_fake_print_request("Create QR for github.com")

    assert print_request.intent is Intent.QR
    assert print_request.status is Status.PROCESSING
    assert label_data.label_type is LabelType.QR
    assert label_data.qr_data == "github.com"


def test_state_machine_supports_happy_path_back_to_ready():
    state_machine = StateMachine()

    for next_state in [
        DeviceState.READY,
        DeviceState.LISTENING,
        DeviceState.PROCESSING,
        DeviceState.PREVIEW,
        DeviceState.PRINTING,
        DeviceState.DONE,
        DeviceState.READY,
    ]:
        state_machine.transition_to(next_state)

    assert state_machine.current_state is DeviceState.READY


def test_state_machine_rejects_invalid_transition():
    state_machine = StateMachine(initial_state=DeviceState.READY)

    with pytest.raises(ValueError):
        state_machine.transition_to(DeviceState.PRINTING)
