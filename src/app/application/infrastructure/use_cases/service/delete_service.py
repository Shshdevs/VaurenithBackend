from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import ServiceNotFound
from app.application.infrastructure.interfaces import ServiceRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteService:
    def __init__(
        self, service_repository: ServiceRepository, recorder: ChangeRecorder
    ) -> None:
        self._service_repository = service_repository
        self._recorder = recorder

    async def execute(self, identity: VerifiedIdentity, service_id: UUID) -> None:
        existing = await self._service_repository.get_by_id(identity, service_id)
        if existing is None:
            raise ServiceNotFound(str(service_id))
        if not await self._service_repository.delete(identity, service_id):
            raise ServiceNotFound(str(service_id))
        await self._recorder.execute(
            identity,
            EntityType.SERVICE,
            service_id,
            ChangeOperation.DELETE,
            existing.version + 1,
        )
