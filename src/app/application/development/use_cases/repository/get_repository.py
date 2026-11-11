from uuid import UUID

from app.application.development.dto import RepositoryData
from app.application.development.exceptions import RepositoryNotFound
from app.application.development.interfaces import RepositoryRepository
from app.application.identity import VerifiedIdentity


class GetRepository:
    def __init__(self, repository_repository: RepositoryRepository) -> None:
        self._repository_repository = repository_repository

    async def get_repository(
        self, identity: VerifiedIdentity, repository_id: UUID
    ) -> RepositoryData:
        repository = await self._repository_repository.get_by_id(
            identity.user_id, repository_id
        )
        if repository is None:
            raise RepositoryNotFound(str(repository_id))
        return RepositoryData.from_repository(repository)
