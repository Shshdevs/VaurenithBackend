from datetime import datetime
from typing import Any
from uuid import UUID

from app.api.schemas.common import Schema
from app.domain.infrastructure.enums import DbmsType, ResourceStatus


class DatabaseData(Schema):
    id: UUID
    project_id: UUID | None
    environment_id: UUID | None
    device_id: UUID
    container_id: UUID | None
    service_id: UUID | None
    name: str
    slug: str
    dbms_type: DbmsType
    host: str | None
    port: int | None
    database_name: str | None
    status: ResourceStatus
    last_checked_at: datetime | None
    metadata: dict[str, Any] | None
    version: int
    created_at: datetime
    updated_at: datetime
