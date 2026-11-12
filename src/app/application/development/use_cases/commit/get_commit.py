from uuid import UUID

from app.application.development.dto import CommitData
from app.application.development.exceptions import CommitNotFound
from app.application.development.interfaces import CommitRepository
from app.application.identity import VerifiedIdentity


class GetCommit:
    def __init__(self, repository: CommitRepository) -> None:
        self._repository = repository

    async def get_commit(self, identity: VerifiedIdentity, commit_id: UUID) -> CommitData:
        commit = await self._repository.get_by_id(identity.user_id, commit_id)
        if commit is None:
            raise CommitNotFound(str(commit_id))
        return CommitData.from_commit(commit)
