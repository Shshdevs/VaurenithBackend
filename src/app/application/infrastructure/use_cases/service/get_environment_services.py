from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ServiceData
from app.application.infrastructure.interfaces import ServiceRepository


class GetEnvironmentServices:
    def __init__(self, service_repository: ServiceRepository) -> None:
        self._service_repository = service_repository

    async def execute(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[ServiceData]:
        services = await self._service_repository.get_by_environment(
            identity, environment_id
        )
        return [ServiceData.from_service(service) for service in services]
