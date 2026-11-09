from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectNotFound
from app.application.projects.interfaces import ProjectRepository


class ProjectAccess:
    def __init__(self, project_repository: ProjectRepository) -> None:
        self._project_repository = project_repository

    async def require_project(self, identity: VerifiedIdentity, project_id: UUID) -> None:
        project = await self._project_repository.get_by_id(
            user_id=identity.user_id,
            project_id=project_id,
        )
        if project is None:
            raise ProjectNotFound(str(project_id))

    async def get_user_project_ids(self, identity: VerifiedIdentity) -> set[UUID]:
        projects = await self._project_repository.get_user_projects(identity.user_id)
        return {project.id for project in projects}
