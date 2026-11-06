from app.application.common.exceptions import NotFound


class ProjectNotFound(NotFound):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project with id {project_id} not found")
