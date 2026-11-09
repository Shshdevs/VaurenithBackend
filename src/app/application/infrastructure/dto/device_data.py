from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.infrastructure import Device
from app.domain.infrastructure.enums import DeviceType


@dataclass(frozen=True)
class DeviceData:
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

    @classmethod
    def from_device(cls, device: Device) -> DeviceData:
        return cls(
            id=device.id,
            user_id=device.user_id,
            name=device.name,
            slug=device.slug,
            hostname=device.hostname,
            description=device.description,
            device_type=device.device_type,
            operating_system=device.operating_system,
            os_version=device.os_version,
            architecture=device.architecture,
            tags=device.tags,
            last_seen_at=device.last_seen_at,
            last_status_at=device.last_status_at,
            version=device.version,
            created_at=device.created_at,
            updated_at=device.updated_at,
            deleted_at=device.deleted_at,
        )
