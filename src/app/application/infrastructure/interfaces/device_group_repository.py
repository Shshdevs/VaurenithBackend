from typing import Protocol
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.infrastructure import DeviceGroup


class DeviceGroupRepository(Protocol):
    async def get_by_id(
        self, identity: VerifiedIdentity, device_group_id: UUID
    ) -> DeviceGroup | None: ...
    async def create(self, device_group: DeviceGroup) -> None: ...
    async def update(
        self, identity: VerifiedIdentity, device_group: DeviceGroup
    ) -> bool: ...
    async def delete(self, identity: VerifiedIdentity, device_group_id: UUID) -> bool: ...
