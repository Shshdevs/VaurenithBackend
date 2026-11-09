from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.infrastructure import Service
from app.domain.infrastructure.enums import ResourceStatus, ServiceType


@dataclass(frozen=True)
class ServiceData:
    id: UUID
    project_id: UUID | None
    environment_id: UUID | None
    device_id: UUID
    name: str
    slug: str
    service_type: ServiceType
    description: str | None
    system_identifier: str | None
    status: ResourceStatus
    last_status_at: datetime | None
    metadata: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_service(cls, service: Service) -> ServiceData:
        return cls(
            id=service.id,
            project_id=service.project_id,
            environment_id=service.environment_id,
            device_id=service.device_id,
            name=service.name,
            slug=service.slug,
            service_type=service.service_type,
            description=service.description,
            system_identifier=service.system_identifier,
            status=service.status,
            last_status_at=service.last_status_at,
            metadata=service.metadata,
            version=service.version,
            created_at=service.created_at,
            updated_at=service.updated_at,
        )
