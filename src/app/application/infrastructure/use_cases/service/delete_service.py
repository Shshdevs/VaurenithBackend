from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import ServiceNotFound
from app.application.infrastructure.interfaces import ServiceRepository


class DeleteService:
    def __init__(self, service_repository: ServiceRepository) -> None:
        self._service_repository = service_repository

    async def execute(self, identity: VerifiedIdentity, service_id: UUID) -> None:
        if not await self._service_repository.delete(identity, service_id):
            raise ServiceNotFound(str(service_id))
