from datetime import UTC, datetime
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ServiceData
from app.application.infrastructure.exceptions import (
    ServiceNotFound,
    ServiceVersionConflict,
)
from app.application.infrastructure.interfaces import ServiceRepository
from app.domain.infrastructure import InvalidService, Service
from app.domain.infrastructure.enums import ResourceStatus


class UpdateServiceStatus:
    def __init__(self, service_repository: ServiceRepository) -> None:
        self._service_repository = service_repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        service_id: UUID,
        expected_version: int,
        status: ResourceStatus,
    ) -> ServiceData:
        existing = await self._service_repository.get_by_id(identity, service_id)
        if existing is None:
            raise ServiceNotFound(str(service_id))
        if existing.version != expected_version:
            raise ServiceVersionConflict(expected_version, existing.version)

        now = datetime.now(UTC)
        try:
            service = Service(
                entity_id=existing.id,
                project_id=existing.project_id,
                environment_id=existing.environment_id,
                device_id=existing.device_id,
                name=existing.name_value,
                service_type=existing.service_type,
                description=existing.description,
                system_identifier=existing.system_identifier_value,
                status=status,
                last_status_at=now,
                metadata=existing.metadata,
                version=expected_version + 1,
                created_at=existing.created_at,
                updated_at=now,
            )
        except InvalidService as error:
            raise InvalidInput(str(error)) from error
        updated = await self._service_repository.update(identity, service, expected_version)
        if not updated:
            latest = await self._service_repository.get_by_id(identity, service_id)
            if latest is None:
                raise ServiceNotFound(str(service_id))
            raise ServiceVersionConflict(expected_version, latest.version)
        return ServiceData.from_service(service)
