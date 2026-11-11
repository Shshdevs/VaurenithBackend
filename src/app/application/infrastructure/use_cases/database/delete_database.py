from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DatabaseNotFound
from app.application.infrastructure.interfaces import DatabaseRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization.enums import ChangeOperation


class DeleteDatabase:
    def __init__(
        self,
        database_repository: DatabaseRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._database_repository = database_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(self, identity: VerifiedIdentity, database_id: UUID) -> None:
        existing = await self._database_repository.get_by_id(identity, database_id)
        if existing is None:
            raise DatabaseNotFound(str(database_id))
        if not await self._database_repository.delete(identity, database_id):
            raise DatabaseNotFound(str(database_id))
        await self._recorder.execute(
            identity,
            EntityType.DATABASE,
            database_id,
            ChangeOperation.DELETE,
            existing.version + 1,
        )
