from app.application.common.exceptions import Conflict, NotFound


class SettingNotFound(NotFound):
    def __init__(self, setting_id: str) -> None:
        super().__init__(f"Setting with id {setting_id} not found")


class ClientDeviceNotFound(NotFound):
    def __init__(self, client_device_id: str) -> None:
        super().__init__(f"Client device with id {client_device_id} not found")


class SettingAlreadyExists(Conflict):
    def __init__(self) -> None:
        super().__init__("Setting with this scope and key already exists")


class SettingVersionConflict(Conflict):
    def __init__(self, expected_version: int, current_version: int | None = None) -> None:
        message = f"Setting version conflict: expected version {expected_version} is stale"
        if current_version is not None:
            message += f"; current version is {current_version}"
        super().__init__(message)
