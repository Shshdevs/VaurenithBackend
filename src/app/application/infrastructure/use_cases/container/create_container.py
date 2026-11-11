from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ContainerData
from app.application.infrastructure.exceptions import ContainerAssociationNotFound
from app.application.infrastructure.interfaces import ContainerRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import (
    Container,
    ContainerImage,
    ContainerName,
    ContainerRuntimeId,
    ContainerStatus,
    InvalidContainer,
)
from app.domain.synchronization.enums import ChangeOperation


class CreateContainer:
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
    async def execute(
        self,
        identity: VerifiedIdentity,
        device_id: UUID,
        container_runtime_id: str,
        name: str,
        project_id: UUID | None = None,
        environment_id: UUID | None = None,
        service_id: UUID | None = None,
        image: str | None = None,
        status: ContainerStatus = ContainerStatus.UNKNOWN,
        ports: dict[str, Any] | None = None,
        volumes: dict[str, Any] | None = None,
        networks: dict[str, Any] | None = None,
        started_at: datetime | None = None,
        last_seen_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ContainerData:
        now = datetime.now(UTC)
        try:
            container = Container(
                entity_id=uuid4(),
                device_id=device_id,
                container_runtime_id=ContainerRuntimeId(container_runtime_id),
                name=ContainerName(name),
                created_at=now,
                updated_at=now,
                project_id=project_id,
                environment_id=environment_id,
                service_id=service_id,
                image=ContainerImage(image) if image is not None else None,
                status=status,
                ports=ports,
                volumes=volumes,
                networks=networks,
                started_at=started_at,
                last_seen_at=last_seen_at,
                metadata=metadata,
            )
        except InvalidContainer as error:
            raise InvalidInput(str(error)) from error

        if not await self._container_repository.create(identity, container):
            raise ContainerAssociationNotFound()

        await self._recorder.execute(
            identity,
            EntityType.CONTAINER,
            container.id,
            ChangeOperation.INSERT,
            container.version,
            {
                "container_runtime_id": container.container_runtime_id,
                "device_id": str(container.device_id),
                "project_id": str(container.project_id)
                if container.project_id is not None
                else None,
                "environment_id": str(container.environment_id)
                if container.environment_id is not None
                else None,
                "service_id": str(container.service_id)
                if container.service_id is not None
                else None,
                "name": container.name,
                "image": container.image,
                "status": container.status.value,
                "ports": container.ports,
                "volumes": container.volumes,
                "networks": container.networks,
                "started_at": container.started_at.isoformat()
                if container.started_at is not None
                else None,
                "last_seen_at": container.last_seen_at.isoformat()
                if container.last_seen_at is not None
                else None,
            },
        )

        return ContainerData.from_container(container)
