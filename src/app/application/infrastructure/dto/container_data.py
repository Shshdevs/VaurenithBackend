from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.infrastructure import Container


@dataclass(frozen=True)
class ContainerData:
    id: UUID
    project_id: UUID | None
    environment_id: UUID | None
    device_id: UUID | None
    service_id: UUID | None
    container_runtime_id: str
    name: str
    slug: str
    image: str | None
    status: str
    ports: dict[str, Any] | None
    volumes: dict[str, Any] | None
    networks: dict[str, Any] | None
    started_at: datetime | None
    last_seen_at: datetime | None
    metadata: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_container(cls, container: Container) -> ContainerData:
        return ContainerData(
            id=container.id,
            project_id=container.project_id,
            environment_id=container.environment_id,
            device_id=container.device_id,
            service_id=container.service_id,
            container_runtime_id=container.container_runtime_id,
            name=container.name,
            slug=container.slug,
            image=container.image,
            status=container.status,
            ports=container.ports,
            volumes=container.volumes,
            networks=container.networks,
            started_at=container.started_at,
            last_seen_at=container.last_seen_at,
            metadata=container.metadata,
            version=container.version,
            created_at=container.created_at,
            updated_at=container.updated_at,
        )
