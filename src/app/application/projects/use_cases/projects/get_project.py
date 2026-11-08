from uuid import UUID

from app.application.identity.dto import VerifiedIdentity
from app.application.projects.dto import ProjectData
from app.application.projects.exceptions import ProjectNotFound
from app.application.projects.interfaces import ProjectRepository


class GetProject:
    def __init__(self, project_repository: ProjectRepository) -> None:
        self._project_repository = project_repository

    async def execute(self, identity: VerifiedIdentity, project_id: UUID) -> ProjectData:
        project = await self._project_repository.get_by_id(
            user_id=identity.user_id,
            project_id=project_id,
        )

        if not project:
            raise ProjectNotFound(str(project_id))
        return ProjectData.from_project(project)
