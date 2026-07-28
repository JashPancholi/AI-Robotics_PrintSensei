from app.enums.device_state import DeviceState


class StateMachine:
    _transitions: dict[DeviceState, set[DeviceState]] = {
        DeviceState.BOOTING: {DeviceState.READY},
        DeviceState.READY: {DeviceState.MENU, DeviceState.LISTENING},
        DeviceState.MENU: {DeviceState.READY, DeviceState.LISTENING},
        DeviceState.LISTENING: {DeviceState.PROCESSING},
        DeviceState.PROCESSING: {DeviceState.PREVIEW, DeviceState.ERROR},
        DeviceState.PREVIEW: {DeviceState.PRINTING, DeviceState.READY},
        DeviceState.PRINTING: {DeviceState.DONE, DeviceState.ERROR},
        DeviceState.DONE: {DeviceState.READY},
        DeviceState.ERROR: {DeviceState.READY},
    }

    def __init__(self, initial_state: DeviceState = DeviceState.BOOTING) -> None:
        self.current_state = initial_state

    def can_transition(self, next_state: DeviceState) -> bool:
        return next_state in self._transitions[self.current_state]

    def transition_to(self, next_state: DeviceState) -> DeviceState:
        if not self.can_transition(next_state):
            raise ValueError(
                f"Cannot transition from {self.current_state.value} to {next_state.value}"
            )

        self.current_state = next_state
        return self.current_state
