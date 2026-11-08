from uuid import UUID

from app.application.identity.dto import VerifiedIdentity
from app.application.projects.exceptions import ProjectNotFound
from app.application.projects.interfaces import ProjectRepository


class DeleteProject:
    def __init__(self, project_repository: ProjectRepository) -> None:
        self._project_repository = project_repository

    async def execute(self, identity: VerifiedIdentity, project_id: UUID) -> None:
        result = await self._project_repository.delete(
            identity.user_id, project_id=project_id
        )
        if not result:
            raise ProjectNotFound(str(project_id))
