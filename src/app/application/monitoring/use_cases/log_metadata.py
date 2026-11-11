from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import (
    ContainerNotFound,
    DeviceNotFound,
    ServiceNotFound,
)
from app.application.infrastructure.interfaces import (
    ContainerRepository,
    DeviceRepository,
    ServiceRepository,
)
from app.application.monitoring.dto import LogMetadataData
from app.application.monitoring.interfaces import LogMetadataRepository
from app.application.projects.exceptions import ProjectNotFound
from app.application.projects.interfaces import ProjectRepository
from app.domain.monitoring import InvalidLogMetadata, LogMetadata


class CreateLogMetadata:
    def __init__(
        self,
        repository: LogMetadataRepository,
        project_repository: ProjectRepository,
        device_repository: DeviceRepository,
        service_repository: ServiceRepository,
        container_repository: ContainerRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._project_repository = project_repository
        self._device_repository = device_repository
        self._service_repository = service_repository
        self._container_repository = container_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def create_log_metadata(
        self,
        identity: VerifiedIdentity,
        source: str,
        project_id: UUID | None,
        device_id: UUID | None,
        service_id: UUID | None,
        container_id: UUID | None,
        reference: str | None,
        description: str | None,
        severity: str | None,
        records_count: int | None,
        collected_at: datetime | None,
    ) -> LogMetadataData:
        project = None
        device = None
        service = None
        container = None
        if project_id is not None:
            project = await self._project_repository.get_by_id(identity.user_id, project_id)
            if project is None:
                raise ProjectNotFound(str(project_id))
        if device_id is not None:
            device = await self._device_repository.get_by_id(identity, device_id)
            if device is None:
                raise DeviceNotFound(str(device_id))
        if service_id is not None:
            service = await self._service_repository.get_by_id(identity, service_id)
            if service is None:
                raise ServiceNotFound(str(service_id))
        if container_id is not None:
            container = await self._container_repository.get_by_id(identity, container_id)
            if container is None:
                raise ContainerNotFound(str(container_id))

        if device is not None and service is not None and service.device_id != device.id:
            raise InvalidInput("Service does not belong to the specified device")
        if (
            device is not None
            and container is not None
            and container.device_id != device.id
        ):
            raise InvalidInput("Container does not belong to the specified device")
        if (
            service is not None
            and container is not None
            and container.service_id != service.id
        ):
            raise InvalidInput("Container does not belong to the specified service")
        if (
            project is not None
            and service is not None
            and service.project_id is not None
            and service.project_id != project.id
        ):
            raise InvalidInput("Service does not belong to the specified project")
        if (
            project is not None
            and container is not None
            and container.project_id is not None
            and container.project_id != project.id
        ):
            raise InvalidInput("Container does not belong to the specified project")
        if not source.strip():
            raise InvalidInput("Log source must not be empty")

        try:
            value = LogMetadata(
                entity_id=uuid4(),
                user_id=identity.user_id,
                source=source,
                created_at=datetime.now(UTC),
                project_id=project_id,
                device_id=device_id,
                service_id=service_id,
                container_id=container_id,
                reference=reference,
                description=description,
                severity=severity,
                records_count=records_count,
                collected_at=collected_at,
            )
        except InvalidLogMetadata as error:
            raise InvalidInput(str(error)) from error
        await self._repository.create(value)
        return LogMetadataData.from_log_metadata(value)


class GetUserLogMetadata:
    def __init__(self, repository: LogMetadataRepository) -> None:
        self._repository = repository

    async def get_user_log_metadata(
        self,
        identity: VerifiedIdentity,
        project_id: UUID | None,
        device_id: UUID | None,
        service_id: UUID | None,
        container_id: UUID | None,
        source: str | None,
        severity: str | None,
        start: datetime | None,
        end: datetime | None,
        limit: int,
        offset: int,
    ) -> list[LogMetadataData]:
        if any(
            boundary is not None
            and (boundary.tzinfo is None or boundary.utcoffset() is None)
            for boundary in (start, end)
        ):
            raise InvalidInput("Log metadata range boundaries must include a timezone")
        if start is not None and end is not None and start >= end:
            raise InvalidInput("Log metadata range start must precede end")
        values = await self._repository.get_user_log_metadata(
            identity.user_id,
            project_id,
            device_id,
            service_id,
            container_id,
            source,
            severity,
            start,
            end,
            limit,
            offset,
        )
        return [LogMetadataData.from_log_metadata(value) for value in values]
