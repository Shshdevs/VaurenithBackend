from app.application.common.exceptions import Conflict, NotFound


class DeviceNotFound(NotFound):
    def __init__(self, device_id: str) -> None:
        super().__init__(f"Device with id {device_id} not found")


class ConnectionNotFound(NotFound):
    def __init__(self, connection_id: str) -> None:
        super().__init__(f"Connection with id {connection_id} not found")


class ConnectionDeviceNotFound(NotFound):
    def __init__(self, device_id: str) -> None:
        super().__init__(f"Device with id {device_id} not found")


class ConnectionVersionConflict(Conflict):
    def __init__(self, expected_version: int, current_version: int | None = None) -> None:
        message = (
            f"Connection version conflict: expected version {expected_version} is stale"
        )
        if current_version is not None:
            message += f"; current version is {current_version}"
        super().__init__(message)


class DefaultConnectionConflict(Conflict):
    def __init__(self) -> None:
        super().__init__("The device already has a default connection")


class DeviceVersionConflict(Conflict):
    def __init__(self, expected_version: int, current_version: int | None = None) -> None:
        message = f"Device version conflict: expected version {expected_version} is stale"
        if current_version is not None:
            message += f"; current version is {current_version}"
        super().__init__(message)


class ServiceNotFound(NotFound):
    def __init__(self, service_id: str) -> None:
        super().__init__(f"Service with id {service_id} not found")


class ServiceAssociationNotFound(NotFound):
    def __init__(self) -> None:
        super().__init__("One or more service associations were not found")


class ServiceVersionConflict(Conflict):
    def __init__(self, expected_version: int, current_version: int | None = None) -> None:
        message = f"Service version conflict: expected version {expected_version} is stale"
        if current_version is not None:
            message += f"; current version is {current_version}"
        super().__init__(message)


class ContainerDeletionConflict(Conflict):
    def __init__(self, container_id: str) -> None:
        super().__init__(f"Container with id {container_id} has dependent records")


class ContainerNotFound(NotFound):
    def __init__(self, container_id: str) -> None:
        super().__init__(f"Container with id {container_id} not found")


class ContainerAssociationNotFound(NotFound):
    def __init__(self) -> None:
        super().__init__("One or more service associations were not found")


class ContainerVersionConflict(Conflict):
    def __init__(self, expected_version: int, current_version: int | None = None) -> None:
        message = (
            f"Container version conflict: expected version {expected_version} is stale"
        )
        if current_version is not None:
            message += f"; current version is {current_version}"
        super().__init__(message)


class ServiceDeletionConflict(Conflict):
    def __init__(self, service_id: str) -> None:
        super().__init__(f"Service with id {service_id} has dependent records")


class DeviceGroupNotFound(NotFound):
    def __init__(self, device_group_id: str) -> None:
        super().__init__(f"DeviceGroup with id {device_group_id} not found")


class DeviceGroupDeletionConflict(Conflict):
    def __init__(self, device_group_id: str) -> None:
        super().__init__(f"DeviceGroup with id {device_group_id} has dependent records")


class DeviceGroupAlreadyExists(Conflict):
    def __init__(self, name: str) -> None:
        super().__init__(f"Device group with name {name} already exists")
