from app.application.common.exceptions import Conflict, NotFound


class ProjectNotFound(NotFound):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project with id {project_id} not found")


class ProjectDeletionConflict(Conflict):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project with id {project_id} has dependent records")


class EnvironmentNotFound(NotFound):
    def __init__(self, environment_id: str) -> None:
        super().__init__(f"Environment with id {environment_id} not found")


class EnvironmentDeletionConflict(Conflict):
    def __init__(self, environment_id: str) -> None:
        super().__init__(f"Environment with id {environment_id} has dependent records")
