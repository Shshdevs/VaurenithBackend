from uuid import UUID

from app.application.development.dto import BranchData
from app.application.development.exceptions import RepositoryNotFound
from app.application.development.interfaces import BranchRepository, RepositoryRepository
from app.application.identity import VerifiedIdentity


class GetRepositoryBranches:
    def __init__(
        self,
        branch_repository: BranchRepository,
        repository_repository: RepositoryRepository,
    ) -> None:
        self._branches = branch_repository
        self._repositories = repository_repository

    async def get_repository_branches(
        self, identity: VerifiedIdentity, repository_id: UUID
    ) -> list[BranchData]:
        if await self._repositories.get_by_id(identity.user_id, repository_id) is None:
            raise RepositoryNotFound(str(repository_id))
        branches = await self._branches.get_by_repository(identity.user_id, repository_id)
        return [BranchData.from_branch(branch) for branch in branches]
