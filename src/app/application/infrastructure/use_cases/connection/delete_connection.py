from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import ConnectionNotFound
from app.application.infrastructure.interfaces import ConnectionRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization.enums import ChangeOperation


class DeleteConnection:
    def __init__(
        self,
        connection_repository: ConnectionRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._connection_repository = connection_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(self, identity: VerifiedIdentity, connection_id: UUID) -> None:
        existing = await self._connection_repository.get_by_id(identity, connection_id)
        if existing is None:
            raise ConnectionNotFound(str(connection_id))
        if not await self._connection_repository.delete(identity, connection_id):
            raise ConnectionNotFound(str(connection_id))
        await self._recorder.execute(
            identity,
            EntityType.CONNECTION,
            connection_id,
            ChangeOperation.DELETE,
            existing.version + 1,
        )
