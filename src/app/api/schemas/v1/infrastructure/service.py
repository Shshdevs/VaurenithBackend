from datetime import datetime
from typing import Any
from uuid import UUID

from app.api.schemas.common import Schema
from app.domain.infrastructure.enums import ResourceStatus, ServiceType


class ServiceData(Schema):
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
