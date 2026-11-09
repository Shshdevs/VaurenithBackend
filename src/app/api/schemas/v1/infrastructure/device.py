from datetime import datetime
from uuid import UUID

from app.api.schemas.common import Schema
from app.domain.infrastructure.enums import DeviceType


class Device(Schema):
    id: UUID
    user_id: UUID
    name: str
    slug: str
    hostname: str | None
    description: str | None
    device_type: DeviceType
    operating_system: str | None
    os_version: str | None
    architecture: str | None
    tags: list[str] | None
    last_seen_at: datetime | None
    last_status_at: datetime | None
    version: int
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None
