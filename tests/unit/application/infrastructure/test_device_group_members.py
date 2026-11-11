from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpUnitOfWork

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import (
    DeviceGroupMemberAlreadyExists,
    DeviceGroupMemberNotFound,
    DeviceGroupNotFound,
    DeviceNotFound,
)
from app.application.infrastructure.use_cases.device_group import (
    AddDeviceGroupMember,
    GetDeviceGroupMembers,
    RemoveDeviceGroupMember,
)
from app.domain.common.enums import EntityType
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import (
    Device,
    DeviceGroup,
    DeviceGroupMember,
    DeviceGroupName,
    DeviceName,
    DeviceType,
)
from app.domain.synchronization import ChangeOperation


class FakeGroupRepository:
    def __init__(self, groups: list[DeviceGroup]) -> None:
        self.groups = {group.id: group for group in groups}

    async def get_by_id(
        self, identity: VerifiedIdentity, group_id: UUID
    ) -> DeviceGroup | None:
        group = self.groups.get(group_id)
        return group if group is not None and group.user_id == identity.user_id else None


class FakeDeviceRepository:
    def __init__(self, devices: list[Device]) -> None:
        self.devices = {device.id: device for device in devices}

    async def get_by_id(self, identity: VerifiedIdentity, device_id: UUID) -> Device | None:
        device = self.devices.get(device_id)
        return device if device is not None and device.user_id == identity.user_id else None


class FakeMemberRepository:
    def __init__(self, members: list[DeviceGroupMember] | None = None) -> None:
        self.members = {
            (member.group_id, member.device_id): member for member in members or []
        }

    async def get_by_group(
        self, identity: VerifiedIdentity, group_id: UUID
    ) -> list[DeviceGroupMember]:
        return [
            member
            for (member_group_id, _), member in self.members.items()
            if member_group_id == group_id
        ]

    async def get_by_device(
        self, identity: VerifiedIdentity, group_id: UUID, device_id: UUID
    ) -> DeviceGroupMember | None:
        return self.members.get((group_id, device_id))

    async def add(self, identity: VerifiedIdentity, member: DeviceGroupMember) -> None:
        key = (member.group_id, member.device_id)
        if key in self.members:
            raise DeviceGroupMemberAlreadyExists(
                str(member.group_id), str(member.device_id)
            )
        self.members[key] = member

    async def delete(
        self, identity: VerifiedIdentity, group_id: UUID, device_id: UUID
    ) -> bool:
        return self.members.pop((group_id, device_id), None) is not None


class CapturingRecorder:
    def __init__(self) -> None:
        self.events: list[tuple] = []

    async def execute(self, *args, **kwargs) -> None:
        self.events.append((args, kwargs))


def make_identity(user_id: UUID | None = None) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id or uuid4(),
        email=EmailAddress("group-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("f" * 64),
    )


def make_group(user_id: UUID) -> DeviceGroup:
    now = datetime.now(UTC)
    return DeviceGroup(
        entity_id=uuid4(),
        user_id=user_id,
        name=DeviceGroupName("Production"),
        created_at=now,
        updated_at=now,
    )


def make_device(user_id: UUID) -> Device:
    now = datetime.now(UTC)
    return Device(
        entity_id=uuid4(),
        user_id=user_id,
        name=DeviceName("worker"),
        created_at=now,
        updated_at=now,
        device_type=DeviceType.VPS,
    )


@pytest.mark.anyio
async def test_get_device_group_members_lists_members_after_group_ownership_check() -> None:
    identity = make_identity()
    group = make_group(identity.user_id)
    device = make_device(identity.user_id)
    member = DeviceGroupMember(uuid4(), group.id, device.id, datetime.now(UTC))
    use_case = GetDeviceGroupMembers(
        FakeGroupRepository([group]), FakeMemberRepository([member])
    )

    result = await use_case.list_members(identity, group.id)

    assert [item.id for item in result] == [member.id]
    assert result[0].device_id == device.id


@pytest.mark.anyio
async def test_get_device_group_members_hides_unowned_group() -> None:
    identity = make_identity()
    group = make_group(uuid4())
    use_case = GetDeviceGroupMembers(FakeGroupRepository([group]), FakeMemberRepository())

    with pytest.raises(DeviceGroupNotFound):
        await use_case.list_members(identity, group.id)


@pytest.mark.anyio
async def test_add_device_group_member_records_insert_change() -> None:
    identity = make_identity()
    group = make_group(identity.user_id)
    device = make_device(identity.user_id)
    recorder = CapturingRecorder()
    use_case = AddDeviceGroupMember(
        FakeGroupRepository([group]),
        FakeDeviceRepository([device]),
        FakeMemberRepository(),
        recorder,
        NoOpUnitOfWork(),
    )

    result = await use_case.add(identity, group.id, device.id)

    assert result.group_id == group.id
    assert result.device_id == device.id
    args, _ = recorder.events[0]
    assert args[1:] == (
        EntityType.DEVICE_GROUP_MEMBER,
        result.id,
        ChangeOperation.INSERT,
        1,
        {"group_id": str(group.id), "device_id": str(device.id)},
    )


@pytest.mark.anyio
async def test_add_device_group_member_rejects_unowned_group_or_device() -> None:
    identity = make_identity()
    group = make_group(uuid4())
    owned_group = make_group(identity.user_id)
    foreign_device = make_device(uuid4())
    use_case = AddDeviceGroupMember(
        FakeGroupRepository([group, owned_group]),
        FakeDeviceRepository([foreign_device]),
        FakeMemberRepository(),
        CapturingRecorder(),
        NoOpUnitOfWork(),
    )

    with pytest.raises(DeviceGroupNotFound):
        await use_case.add(identity, group.id, foreign_device.id)
    with pytest.raises(DeviceNotFound):
        await use_case.add(identity, owned_group.id, foreign_device.id)


@pytest.mark.anyio
async def test_add_device_group_member_rejects_duplicate_membership() -> None:
    identity = make_identity()
    group = make_group(identity.user_id)
    device = make_device(identity.user_id)
    existing = DeviceGroupMember(uuid4(), group.id, device.id, datetime.now(UTC))
    use_case = AddDeviceGroupMember(
        FakeGroupRepository([group]),
        FakeDeviceRepository([device]),
        FakeMemberRepository([existing]),
        CapturingRecorder(),
        NoOpUnitOfWork(),
    )

    with pytest.raises(DeviceGroupMemberAlreadyExists):
        await use_case.add(identity, group.id, device.id)


@pytest.mark.anyio
async def test_remove_device_group_member_records_delete_change() -> None:
    identity = make_identity()
    group = make_group(identity.user_id)
    device = make_device(identity.user_id)
    member = DeviceGroupMember(uuid4(), group.id, device.id, datetime.now(UTC))
    member_repository = FakeMemberRepository([member])
    recorder = CapturingRecorder()
    use_case = RemoveDeviceGroupMember(
        FakeGroupRepository([group]), member_repository, recorder, NoOpUnitOfWork()
    )

    await use_case.remove(identity, group.id, device.id)

    assert not member_repository.members
    args, _ = recorder.events[0]
    assert args[1:] == (
        EntityType.DEVICE_GROUP_MEMBER,
        member.id,
        ChangeOperation.DELETE,
        2,
        {"group_id": str(group.id), "device_id": str(device.id)},
    )


@pytest.mark.anyio
async def test_remove_device_group_member_returns_not_found_for_missing_member() -> None:
    identity = make_identity()
    group = make_group(identity.user_id)
    use_case = RemoveDeviceGroupMember(
        FakeGroupRepository([group]),
        FakeMemberRepository(),
        CapturingRecorder(),
        NoOpUnitOfWork(),
    )

    with pytest.raises(DeviceGroupMemberNotFound):
        await use_case.remove(identity, group.id, uuid4())
