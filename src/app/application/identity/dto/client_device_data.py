from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.identity import ClientDevice


@dataclass(frozen=True, slots=True)
class ClientDeviceData:
    id: UUID
    name: str
    platform: str
    app_version: str | None
    status: str
    registered_at: datetime
    last_seen_at: datetime | None
    revoked_at: datetime | None

    @classmethod
    def from_entity(cls, device: ClientDevice) -> ClientDeviceData:
        return cls(
            id=device.id,
            name=device.name,
            platform=device.platform.value,
            app_version=device.app_version,
            status=device.status.value,
            registered_at=device.registered_at,
            last_seen_at=device.last_seen_at,
            revoked_at=device.revoked_at,
        )
