from uuid import UUID

from app.application.development.dto import CommitData
from app.application.development.exceptions import RepositoryNotFound
from app.application.development.interfaces import CommitRepository, RepositoryRepository
from app.application.identity import VerifiedIdentity


class GetRepositoryCommits:
    def __init__(
        self,
        commit_repository: CommitRepository,
        repository_repository: RepositoryRepository,
    ) -> None:
        self._commits = commit_repository
        self._repositories = repository_repository

    async def get_repository_commits(
        self, identity: VerifiedIdentity, repository_id: UUID
    ) -> list[CommitData]:
        if await self._repositories.get_by_id(identity.user_id, repository_id) is None:
            raise RepositoryNotFound(str(repository_id))
        commits = await self._commits.get_by_repository(identity.user_id, repository_id)
        return [CommitData.from_commit(commit) for commit in commits]
