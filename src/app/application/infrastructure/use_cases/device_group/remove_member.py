from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import (
    DeviceGroupMemberNotFound,
    DeviceGroupNotFound,
)
from app.application.infrastructure.interfaces import (
    DeviceGroupMemberRepository,
    DeviceGroupRepository,
)
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class RemoveDeviceGroupMember:
    def __init__(
        self,
        device_group_repository: DeviceGroupRepository,
        member_repository: DeviceGroupMemberRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._device_group_repository = device_group_repository
        self._member_repository = member_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def remove(
        self, identity: VerifiedIdentity, group_id: UUID, device_id: UUID
    ) -> None:
        if await self._device_group_repository.get_by_id(identity, group_id) is None:
            raise DeviceGroupNotFound(str(group_id))
        member = await self._member_repository.get_by_device(identity, group_id, device_id)
        if member is None:
            raise DeviceGroupMemberNotFound(str(group_id), str(device_id))
        if not await self._member_repository.delete(identity, group_id, device_id):
            raise DeviceGroupMemberNotFound(str(group_id), str(device_id))
        await self._recorder.execute(
            identity,
            EntityType.DEVICE_GROUP_MEMBER,
            member.id,
            ChangeOperation.DELETE,
            2,
            {"group_id": str(group_id), "device_id": str(device_id)},
        )
