from app.application.development.dto import RepositoryData
from app.application.development.interfaces import RepositoryRepository
from app.application.identity import VerifiedIdentity


class GetUserRepositories:
    def __init__(self, repository_repository: RepositoryRepository) -> None:
        self._repository_repository = repository_repository

    async def get_user_repositories(
        self, identity: VerifiedIdentity
    ) -> list[RepositoryData]:
        repositories = await self._repository_repository.get_by_user(identity.user_id)
        return [RepositoryData.from_repository(repository) for repository in repositories]
