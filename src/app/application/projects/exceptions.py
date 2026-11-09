from app.application.common.exceptions import Conflict, NotFound


class ProjectNotFound(NotFound):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project with id {project_id} not found")


class ProjectVersionConflict(Conflict):
    def __init__(self, expected_version: int, current_version: int | None = None) -> None:
        message = f"Project version conflict: expected version {expected_version} is stale"
        if current_version is not None:
            message += f"; current version is {current_version}"
        super().__init__(message)


class ProjectDeletionConflict(Conflict):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project with id {project_id} has dependent records")


class EnvironmentNotFound(NotFound):
    def __init__(self, environment_id: str) -> None:
        super().__init__(f"Environment with id {environment_id} not found")


class EnvironmentVersionConflict(Conflict):
    def __init__(self, expected_version: int, current_version: int | None = None) -> None:
        message = (
            f"Environment version conflict: expected version {expected_version} is stale"
        )
        if current_version is not None:
            message += f"; current version is {current_version}"
        super().__init__(message)


class EnvironmentDeletionConflict(Conflict):
    def __init__(self, environment_id: str) -> None:
        super().__init__(f"Environment with id {environment_id} has dependent records")


class ProjectDeviceNotFound(NotFound):
    def __init__(self, project_device_id: str) -> None:
        super().__init__(f"ProjectDevice with id {project_device_id} not found")


class DeviceNotFound(NotFound):
    def __init__(self, device_id: str) -> None:
        super().__init__(f"Device with id {device_id} not found")


class ProjectDeviceDeletionConflict(Conflict):
    def __init__(self, project_device_id: str) -> None:
        super().__init__(f"ProjectDevice with id {project_device_id} has dependent records")
