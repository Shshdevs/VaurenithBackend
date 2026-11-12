from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.exceptions import BranchNotFound
from app.application.development.interfaces import BranchRepository
from app.application.identity import VerifiedIdentity


class DeleteBranch:
    def __init__(self, repository: BranchRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    @transactional
    async def delete_branch(self, identity: VerifiedIdentity, branch_id: UUID) -> None:
        if not await self._repository.delete(identity.user_id, branch_id):
            raise BranchNotFound(str(branch_id))
