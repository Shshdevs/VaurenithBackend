from datetime import datetime
from uuid import UUID

from app.application.common.exceptions import Conflict, InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.dto import BranchData
from app.application.development.exceptions import BranchNotFound
from app.application.development.interfaces import BranchRepository
from app.application.identity import VerifiedIdentity
from app.domain.development.entities.branch import Branch
from app.domain.development.exceptions import InvalidBranch, InvalidCommitHash


class UpdateBranch:
    def __init__(self, repository: BranchRepository, unit_of_work: UnitOfWork) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    @transactional
    async def update_branch(
        self,
        identity: VerifiedIdentity,
        branch_id: UUID,
        name: str,
        commit_hash: str | None,
        is_remote: bool,
        is_current: bool,
        last_updated_at: datetime | None,
        last_synced_at: datetime | None,
    ) -> BranchData:
        existing = await self._repository.get_by_id(identity.user_id, branch_id)
        if existing is None:
            raise BranchNotFound(str(branch_id))
        try:
            branch = Branch(
                entity_id=existing.id,
                repository_id=existing.repository_id,
                name=name,
                commit_hash=commit_hash,
                is_remote=is_remote,
                is_current=is_current,
                last_updated_at=last_updated_at,
                last_synced_at=last_synced_at,
            )
        except (InvalidBranch, InvalidCommitHash, ValueError) as error:
            raise InvalidInput(str(error)) from error
        duplicate = await self._repository.get_by_name(
            identity.user_id, branch.repository_id, branch.name, branch.is_remote
        )
        if duplicate is not None and duplicate.id != branch.id:
            raise Conflict("Branch already exists in this repository")
        if not await self._repository.update(identity.user_id, branch):
            raise BranchNotFound(str(branch_id))
        return BranchData.from_branch(branch)
