from app.application.common.exceptions import Conflict, NotFound


class SyncStateNotFound(NotFound):
    def __init__(self, sync_state_id: str) -> None:
        super().__init__(f"SyncState with id {sync_state_id} not found")


class SyncStateVersionConflict(Conflict):
    def __init__(
        self, expected_version: int | None, current_version: int | None = None
    ) -> None:
        message = (
            f"SyncState version conflict: expected version {expected_version} is stale"
        )
        if current_version is not None:
            message += f"; current version is {current_version}"
        super().__init__(message)


class SyncStateUpdateConflict(Conflict):
    def __init__(self, sync_state_id: str) -> None:
        super().__init__(f"SyncState with id {sync_state_id} was updated concurrently")


class SyncStateAlreadyExists(Conflict):
    def __init__(self) -> None:
        super().__init__("A sync state already exists for this device and entity")


class SyncStateDeletionConflict(Conflict):
    def __init__(self, sync_state_id: str) -> None:
        super().__init__(f"sync_state with id {sync_state_id} has dependent records")
