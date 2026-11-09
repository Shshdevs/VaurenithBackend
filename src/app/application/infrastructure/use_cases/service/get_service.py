from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ServiceData
from app.application.infrastructure.exceptions import ServiceNotFound
from app.application.infrastructure.interfaces import ServiceRepository


class GetService:
    def __init__(self, service_repository: ServiceRepository) -> None:
        self._service_repository = service_repository

    async def execute(self, identity: VerifiedIdentity, service_id: UUID) -> ServiceData:
        service = await self._service_repository.get_by_id(identity, service_id)
        if service is None:
            raise ServiceNotFound(str(service_id))
        return ServiceData.from_service(service)
