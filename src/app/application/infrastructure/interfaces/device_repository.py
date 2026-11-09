from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.infrastructure import Device


class DeviceRepository(Protocol):
    async def get_by_id(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> Device | None: ...

    async def get_by_user(self, identity: VerifiedIdentity) -> list[Device]: ...

    async def create(self, device: Device) -> None: ...

    async def update(
        self, identity: VerifiedIdentity, device: Device, expected_version: int
    ) -> bool: ...

    async def delete(
        self, identity: VerifiedIdentity, device_id: UUID, deleted_at: datetime
    ) -> bool: ...
