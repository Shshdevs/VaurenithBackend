from typing import Protocol
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.infrastructure import DeviceGroupMember


class DeviceGroupMemberRepository(Protocol):
    async def get_by_group(
        self, identity: VerifiedIdentity, group_id: UUID
    ) -> list[DeviceGroupMember]: ...

    async def get_by_device(
        self, identity: VerifiedIdentity, group_id: UUID, device_id: UUID
    ) -> DeviceGroupMember | None: ...

    async def add(self, identity: VerifiedIdentity, member: DeviceGroupMember) -> None: ...

    async def delete(
        self, identity: VerifiedIdentity, group_id: UUID, device_id: UUID
    ) -> bool: ...
