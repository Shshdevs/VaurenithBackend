from app.application.common.exceptions import Conflict, NotFound


class DeviceNotFound(NotFound):
    def __init__(self, device_id: str) -> None:
        super().__init__(f"Device with id {device_id} not found")


class DeviceGroupNotFound(NotFound):
    def __init__(self, device_group_id: str) -> None:
        super().__init__(f"DeviceGroup with id {device_group_id} not found")


class DeviceGroupDeletionConflict(Conflict):
    def __init__(self, device_group_id: str) -> None:
        super().__init__(f"DeviceGroup with id {device_group_id} has dependent records")


class DeviceGroupAlreadyExists(Conflict):
    def __init__(self, name: str) -> None:
        super().__init__(f"Device group with name {name} already exists")
