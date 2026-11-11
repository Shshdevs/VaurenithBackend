from app.application.common.exceptions import Conflict, NotFound


class RepositoryNotFound(NotFound):
    def __init__(self, repository_id: str) -> None:
        super().__init__(f"Repository with id {repository_id} not found")


class RepositoryVersionConflict(Conflict):
    def __init__(self, expected_version: int, current_version: int | None = None) -> None:
        message = (
            f"Repository version conflict: expected version {expected_version} is stale"
        )
        if current_version is not None:
            message += f"; current version is {current_version}"
        super().__init__(message)
