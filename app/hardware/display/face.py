from app.enums.device_state import DeviceState


class FaceRenderer:
    """Returns compact expression names for display adapters."""

    _faces = {
        DeviceState.READY: "ready",
        DeviceState.LISTENING: "listening",
        DeviceState.PROCESSING: "thinking",
        DeviceState.PRINTING: "printing",
        DeviceState.ERROR: "error",
    }

    def face_for(self, state: DeviceState) -> str:
        return self._faces.get(state, "ready")
