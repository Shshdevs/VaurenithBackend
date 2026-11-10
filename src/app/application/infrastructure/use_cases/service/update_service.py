from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ServiceData
from app.application.infrastructure.exceptions import (
    ServiceAssociationNotFound,
    ServiceNotFound,
    ServiceVersionConflict,
)
from app.application.infrastructure.interfaces import ServiceRepository
from app.application.infrastructure.use_cases.service.system_identifier import (
    build_system_identifier,
)
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import InvalidService, Service, ServiceName
from app.domain.infrastructure.enums import ServiceType
from app.domain.synchronization import ChangeOperation


class UpdateService:
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
        device_id: UUID,
        name: str,
        service_type: ServiceType,
        project_id: UUID | None = None,
        environment_id: UUID | None = None,
        description: str | None = None,
        system_identifier: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ServiceData:
        existing = await self._service_repository.get_by_id(identity, service_id)
        if existing is None:
            raise ServiceNotFound(str(service_id))
        if existing.version != expected_version:
            raise ServiceVersionConflict(expected_version, existing.version)

        try:
            service = Service(
                entity_id=existing.id,
                project_id=project_id,
                environment_id=environment_id,
                device_id=device_id,
                name=ServiceName(name),
                service_type=service_type,
                description=description,
                system_identifier=build_system_identifier(system_identifier),
                status=existing.status,
                last_status_at=existing.last_status_at,
                metadata=metadata,
                version=expected_version + 1,
                created_at=existing.created_at,
                updated_at=datetime.now(UTC),
            )
        except InvalidService as error:
            raise InvalidInput(str(error)) from error

        updated = await self._service_repository.update(identity, service, expected_version)
        if not updated:
            latest = await self._service_repository.get_by_id(identity, service_id)
            if latest is None:
                raise ServiceNotFound(str(service_id))
            if latest.version != expected_version:
                raise ServiceVersionConflict(expected_version, latest.version)
            raise ServiceAssociationNotFound()
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
