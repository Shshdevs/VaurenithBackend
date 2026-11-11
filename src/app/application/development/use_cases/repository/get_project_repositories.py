from uuid import UUID

from app.application.development.dto import RepositoryData
from app.application.development.interfaces import RepositoryRepository
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectNotFound
from app.application.projects.interfaces import ProjectRepository


class GetProjectRepositories:
    def __init__(
        self,
        repository_repository: RepositoryRepository,
        project_repository: ProjectRepository,
    ) -> None:
        self._repository_repository = repository_repository
        self._project_repository = project_repository

    async def get_project_repositories(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[RepositoryData]:
        project = await self._project_repository.get_by_id(identity.user_id, project_id)
        if project is None:
            raise ProjectNotFound(str(project_id))
        repositories = await self._repository_repository.get_by_project(
            identity.user_id, project_id
        )
        return [RepositoryData.from_repository(repository) for repository in repositories]
