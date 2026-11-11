from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import ContainerNotFound
from app.application.infrastructure.interfaces import ContainerRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteContainer:
    def __init__(
        self,
        container_repository: ContainerRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._container_repository = container_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(self, identity: VerifiedIdentity, container_id: UUID) -> None:
        existing = await self._container_repository.get_by_id(identity, container_id)
        if existing is None:
            raise ContainerNotFound(str(container_id))
        if not await self._container_repository.delete(identity, container_id):
            raise ContainerNotFound(str(container_id))
        await self._recorder.execute(
            identity,
            EntityType.CONTAINER,
            container_id,
            ChangeOperation.DELETE,
            existing.version + 1,
        )
