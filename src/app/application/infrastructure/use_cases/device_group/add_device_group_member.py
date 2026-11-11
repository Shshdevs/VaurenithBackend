from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DeviceGroupMemberData
from app.application.infrastructure.exceptions import DeviceGroupNotFound, DeviceNotFound
from app.application.infrastructure.interfaces import (
    DeviceGroupMemberRepository,
    DeviceGroupRepository,
    DeviceRepository,
)
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.infrastructure import DeviceGroupMember
from app.domain.synchronization import ChangeOperation


class AddDeviceGroupMember:
    def __init__(
        self,
        device_group_repository: DeviceGroupRepository,
        device_repository: DeviceRepository,
        member_repository: DeviceGroupMemberRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._device_group_repository = device_group_repository
        self._device_repository = device_repository
        self._member_repository = member_repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def add(
        self, identity: VerifiedIdentity, group_id: UUID, device_id: UUID
    ) -> DeviceGroupMemberData:
        group = await self._device_group_repository.get_by_id(identity, group_id)
        if group is None:
            raise DeviceGroupNotFound(str(group_id))
        device = await self._device_repository.get_by_id(identity, device_id)
        if device is None:
            raise DeviceNotFound(str(device_id))

        member = DeviceGroupMember(
            entity_id=uuid4(),
            group_id=group_id,
            device_id=device_id,
            created_at=datetime.now(UTC),
        )
        await self._member_repository.add(identity, member)
        await self._recorder.execute(
            identity,
            EntityType.DEVICE_GROUP_MEMBER,
            member.id,
            ChangeOperation.INSERT,
            1,
            {"group_id": str(group_id), "device_id": str(device_id)},
        )
        return DeviceGroupMemberData.from_member(member)
