from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.development.exceptions import (
    RepositoryNotFound,
    RepositoryVersionConflict,
)
from app.application.development.interfaces import RepositoryRepository
from app.application.identity import VerifiedIdentity
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteRepository:
    def __init__(
        self,
        repository_repository: RepositoryRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository_repository = repository_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def delete_repository(
        self,
        identity: VerifiedIdentity,
        repository_id: UUID,
        expected_version: int,
    ) -> None:
        existing = await self._repository_repository.get_by_id(
            identity.user_id, repository_id
        )
        if existing is None:
            raise RepositoryNotFound(str(repository_id))
        if existing.version != expected_version:
            raise RepositoryVersionConflict(expected_version, existing.version)
        if not await self._repository_repository.delete(
            identity.user_id, repository_id, expected_version
        ):
            raise RepositoryVersionConflict(expected_version)
        await self._recorder.execute(
            identity,
            EntityType.REPOSITORY,
            existing.id,
            ChangeOperation.DELETE,
            expected_version + 1,
            {"project_id": str(existing.project_id), "name": existing.name},
        )
