from datetime import datetime
from uuid import UUID, uuid4

from app.application.common.exceptions import Conflict, InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.dto import BranchData
from app.application.development.exceptions import RepositoryNotFound
from app.application.development.interfaces import BranchRepository, RepositoryRepository
from app.application.identity import VerifiedIdentity
from app.domain.development.entities.branch import Branch
from app.domain.development.exceptions import InvalidBranch, InvalidCommitHash


class CreateBranch:
    def __init__(
        self,
        branch_repository: BranchRepository,
        repository_repository: RepositoryRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._branches = branch_repository
        self._repositories = repository_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def create_branch(
        self,
        identity: VerifiedIdentity,
        repository_id: UUID,
        name: str,
        commit_hash: str | None = None,
        is_remote: bool = False,
        is_current: bool = False,
        last_updated_at: datetime | None = None,
        last_synced_at: datetime | None = None,
    ) -> BranchData:
        if await self._repositories.get_by_id(identity.user_id, repository_id) is None:
            raise RepositoryNotFound(str(repository_id))
        try:
            branch = Branch(
                entity_id=uuid4(),
                repository_id=repository_id,
                name=name,
                commit_hash=commit_hash,
                is_remote=is_remote,
                is_current=is_current,
                last_updated_at=last_updated_at,
                last_synced_at=last_synced_at,
            )
        except (InvalidBranch, InvalidCommitHash, ValueError) as error:
            raise InvalidInput(str(error)) from error
        duplicate = await self._branches.get_by_name(
            identity.user_id, repository_id, branch.name, branch.is_remote
        )
        if duplicate is not None:
            raise Conflict("Branch already exists in this repository")
        await self._branches.create(identity.user_id, branch)
        return BranchData.from_branch(branch)
