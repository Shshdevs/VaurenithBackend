from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ServiceData
from app.application.infrastructure.exceptions import ServiceAssociationNotFound
from app.application.infrastructure.interfaces import ServiceRepository
from app.application.infrastructure.use_cases.service.system_identifier import (
    build_system_identifier,
)
from app.domain.infrastructure import InvalidService, Service, ServiceName
from app.domain.infrastructure.enums import ResourceStatus, ServiceType


class CreateService:
    def __init__(self, service_repository: ServiceRepository) -> None:
        self._service_repository = service_repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        device_id: UUID,
        name: str,
        service_type: ServiceType,
        project_id: UUID | None = None,
        environment_id: UUID | None = None,
        description: str | None = None,
        system_identifier: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ServiceData:
        now = datetime.now(UTC)
        try:
            service = Service(
                entity_id=uuid4(),
                device_id=device_id,
                project_id=project_id,
                environment_id=environment_id,
                name=ServiceName(name),
                service_type=service_type,
                description=description,
                system_identifier=build_system_identifier(system_identifier),
                status=ResourceStatus.UNKNOWN,
                metadata=metadata,
                created_at=now,
                updated_at=now,
            )
        except InvalidService as error:
            raise InvalidInput(str(error)) from error

        if not await self._service_repository.create(identity, service):
            raise ServiceAssociationNotFound()
        return ServiceData.from_service(service)
