from uuid import UUID

from app.application.development.dto import BranchData
from app.application.development.exceptions import BranchNotFound
from app.application.development.interfaces import BranchRepository
from app.application.identity import VerifiedIdentity


class GetBranch:
    def __init__(self, repository: BranchRepository) -> None:
        self._repository = repository

    async def get_branch(self, identity: VerifiedIdentity, branch_id: UUID) -> BranchData:
        branch = await self._repository.get_by_id(identity.user_id, branch_id)
        if branch is None:
            raise BranchNotFound(str(branch_id))
        return BranchData.from_branch(branch)
