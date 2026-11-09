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
from app.application.synchronization.change_log.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import InvalidService, Service
from app.domain.infrastructure.enums import ResourceStatus
from app.domain.synchronization import ChangeOperation


class UpdateServiceStatus:
    def __init__(
        self, service_repository: ServiceRepository, recorder: ChangeRecorder
    ) -> None:
        self._service_repository = service_repository
        self._recorder = recorder

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
        await self._recorder.execute(
            identity,
            EntityType.SERVICE,
            service.id,
            ChangeOperation.UPDATE,
            service.version,
            {
                "device_id": str(service.device_id),
                "project_id": str(service.project_id) if service.project_id else None,
                "environment_id": str(service.environment_id)
                if service.environment_id
                else None,
                "name": service.name,
                "service_type": service.service_type.value,
                "description": service.description,
                "system_identifier": service.system_identifier,
                "status": service.status.value,
            },
        )
        return ServiceData.from_service(service)
