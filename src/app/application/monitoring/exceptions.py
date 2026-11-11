from app.application.common.exceptions import NotFound


class EventClientDeviceNotFound(NotFound):
    def __init__(self, client_device_id: str) -> None:
        super().__init__(f"Client device with id {client_device_id} not found")
