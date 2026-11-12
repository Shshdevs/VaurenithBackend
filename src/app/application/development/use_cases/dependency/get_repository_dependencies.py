from uuid import UUID

from app.application.development.dto import DependencyData
from app.application.development.exceptions import RepositoryNotFound
from app.application.development.interfaces import (
    DependencyRepository,
    RepositoryRepository,
)
from app.application.identity import VerifiedIdentity


class GetRepositoryDependencies:
    def __init__(
        self,
        dependency_repository: DependencyRepository,
        repository_repository: RepositoryRepository,
    ) -> None:
        self._dependencies = dependency_repository
        self._repositories = repository_repository

    async def get_repository_dependencies(
        self, identity: VerifiedIdentity, repository_id: UUID
    ) -> list[DependencyData]:
        if await self._repositories.get_by_id(identity.user_id, repository_id) is None:
            raise RepositoryNotFound(str(repository_id))
        dependencies = await self._dependencies.get_by_repository(
            identity.user_id, repository_id
        )
        return [DependencyData.from_dependency(item) for item in dependencies]
