from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.infrastructure import DeviceGroup


@dataclass(frozen=True)
class DeviceGroupData:
    id: UUID
    user_id: UUID
    name: str
    slug: str
    description: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_device_group(cls, device_group: DeviceGroup) -> DeviceGroupData:
        return cls(
            id=device_group.id,
            user_id=device_group.user_id,
            name=device_group.name,
            slug=device_group.slug,
            description=device_group.description,
            created_at=device_group.created_at,
            updated_at=device_group.updated_at,
        )
