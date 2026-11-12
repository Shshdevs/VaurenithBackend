from uuid import UUID

from app.application.development.dto import CodeComponentData
from app.application.development.exceptions import RepositoryNotFound
from app.application.development.interfaces import (
    CodeComponentRepository,
    RepositoryRepository,
)
from app.application.identity import VerifiedIdentity


class GetRepositoryCodeComponents:
    def __init__(
        self,
        component_repository: CodeComponentRepository,
        repository_repository: RepositoryRepository,
    ) -> None:
        self._components = component_repository
        self._repositories = repository_repository

    async def get_repository_code_components(
        self, identity: VerifiedIdentity, repository_id: UUID
    ) -> list[CodeComponentData]:
        if await self._repositories.get_by_id(identity.user_id, repository_id) is None:
            raise RepositoryNotFound(str(repository_id))
        components = await self._components.get_by_repository(
            identity.user_id, repository_id
        )
        return [CodeComponentData.from_component(item) for item in components]
