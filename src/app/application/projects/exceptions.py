from app.application.common.exceptions import Conflict, NotFound


class ProjectNotFound(NotFound):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project with id {project_id} not found")


class ProjectDeletionConflict(Conflict):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project with id {project_id} has dependent records")
