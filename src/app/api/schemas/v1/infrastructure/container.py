from datetime import datetime
from typing import Any
from uuid import UUID

from app.api.schemas.common import Schema
from app.domain.infrastructure.enums import ContainerStatus


class ContainerData(Schema):
    id: UUID
    project_id: UUID | None
    environment_id: UUID | None
    device_id: UUID
    service_id: UUID | None
    container_runtime_id: str
    name: str
    slug: str
    image: str | None
    status: ContainerStatus
    ports: dict[str, Any] | None
    volumes: dict[str, Any] | None
    networks: dict[str, Any] | None
    started_at: datetime | None
    last_seen_at: datetime | None
    metadata: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime
