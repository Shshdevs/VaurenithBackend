from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.application.common.exceptions import Conflict, InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.dto import CommitData
from app.application.development.exceptions import RepositoryNotFound
from app.application.development.interfaces import CommitRepository, RepositoryRepository
from app.application.identity import VerifiedIdentity
from app.domain.development.entities.commit import Commit
from app.domain.development.exceptions import InvalidCommit, InvalidCommitHash


class CreateCommit:
    def __init__(
        self,
        commit_repository: CommitRepository,
        repository_repository: RepositoryRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._commits = commit_repository
        self._repositories = repository_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def create_commit(
        self,
        identity: VerifiedIdentity,
        repository_id: UUID,
        commit_hash: str,
        author_name: str | None = None,
        author_email: str | None = None,
        message: str | None = None,
        committed_at: datetime | None = None,
        changed_files: Any | None = None,
    ) -> CommitData:
        if await self._repositories.get_by_id(identity.user_id, repository_id) is None:
            raise RepositoryNotFound(str(repository_id))
        try:
            commit = Commit(
                entity_id=uuid4(),
                repository_id=repository_id,
                hash=commit_hash,
                author_name=author_name,
                author_email=author_email,
                message=message,
                committed_at=committed_at,
                changed_files=changed_files,
                cached_at=datetime.now(UTC),
            )
        except (InvalidCommit, InvalidCommitHash, ValueError) as error:
            raise InvalidInput(str(error)) from error
        if await self._commits.get_by_hash(identity.user_id, repository_id, commit.hash):
            raise Conflict("Commit is already cached for this repository")
        await self._commits.create(identity.user_id, commit)
        return CommitData.from_commit(commit)
