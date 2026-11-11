from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceGroupMemberData
from app.application.infrastructure.exceptions import DeviceGroupNotFound
from app.application.infrastructure.interfaces import (
    DeviceGroupMemberRepository,
    DeviceGroupRepository,
)


class GetDeviceGroupMembers:
    def __init__(
        self,
        device_group_repository: DeviceGroupRepository,
        member_repository: DeviceGroupMemberRepository,
    ) -> None:
        self._device_group_repository = device_group_repository
        self._member_repository = member_repository

    async def list_members(
        self, identity: VerifiedIdentity, group_id: UUID
    ) -> list[DeviceGroupMemberData]:
        if await self._device_group_repository.get_by_id(identity, group_id) is None:
            raise DeviceGroupNotFound(str(group_id))
        members = await self._member_repository.get_by_group(identity, group_id)
        return [DeviceGroupMemberData.from_member(member) for member in members]
