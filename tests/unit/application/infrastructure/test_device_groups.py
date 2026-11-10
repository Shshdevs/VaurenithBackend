from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpRecordChange, NoOpUnitOfWork

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceGroupNotFound
from app.application.infrastructure.use_cases.device_group import (
    CreateDeviceGroup,
    DeleteDeviceGroup,
    GetDeviceGroup,
    UpdateDeviceGroup,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import DeviceGroup, DeviceGroupName


class FakeDeviceGroupRepository:
    def __init__(self, groups: list[DeviceGroup] | None = None) -> None:
        self.groups = {group.id: group for group in groups or []}
        self.created: DeviceGroup | None = None
        self.updated: DeviceGroup | None = None

    async def get_by_id(
        self, identity: VerifiedIdentity, device_group_id: UUID
    ) -> DeviceGroup | None:
        group = self.groups.get(device_group_id)
        return group if group and group.user_id == identity.user_id else None

    async def create(self, device_group: DeviceGroup) -> None:
        self.created = device_group
        self.groups[device_group.id] = device_group

    async def update(self, identity: VerifiedIdentity, device_group: DeviceGroup) -> bool:
        if await self.get_by_id(identity, device_group.id) is None:
            return False
        self.updated = device_group
        self.groups[device_group.id] = device_group
        return True

    async def delete(self, identity: VerifiedIdentity, device_group_id: UUID) -> bool:
        if await self.get_by_id(identity, device_group_id) is None:
            return False
        del self.groups[device_group_id]
        return True


def make_identity(user_id: UUID | None = None) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id or uuid4(),
        email=EmailAddress("device-group-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("c" * 64),
    )


def make_group(user_id: UUID | None = None) -> DeviceGroup:
    now = datetime.now(UTC)
    return DeviceGroup(
        entity_id=uuid4(),
        user_id=user_id or uuid4(),
        name=DeviceGroupName("Production"),
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
async def test_create_device_group_uses_identity_and_returns_data() -> None:
    identity = make_identity()
    repository = FakeDeviceGroupRepository()
    use_case = CreateDeviceGroup(repository, NoOpRecordChange(), NoOpUnitOfWork())

    result = await use_case.execute(
        identity=identity,
        name="  Production  ",
        description="  Main fleet  ",
    )

    assert repository.created is not None
    assert repository.created.user_id == identity.user_id
    assert result.user_id == identity.user_id
    assert result.name == "Production"
    assert result.description == "Main fleet"
    assert result.slug == "production"


@pytest.mark.anyio
async def test_create_device_group_rejects_invalid_name() -> None:
    repository = FakeDeviceGroupRepository()
    use_case = CreateDeviceGroup(repository, NoOpRecordChange(), NoOpUnitOfWork())

    with pytest.raises(InvalidInput):
        await use_case.execute(identity=make_identity(), name="  ", description=None)

    assert repository.created is None


@pytest.mark.anyio
async def test_get_device_group_hides_groups_owned_by_other_users() -> None:
    owner = make_identity()
    group = make_group(owner.user_id)
    use_case = GetDeviceGroup(FakeDeviceGroupRepository([group]))

    result = await use_case.execute(identity=owner, device_group_id=group.id)
    assert result.id == group.id

    with pytest.raises(DeviceGroupNotFound):
        await use_case.execute(identity=make_identity(), device_group_id=group.id)


@pytest.mark.anyio
async def test_update_device_group_preserves_owner_and_creation_time() -> None:
    identity = make_identity()
    group = make_group(identity.user_id)
    repository = FakeDeviceGroupRepository([group])
    use_case = UpdateDeviceGroup(repository, NoOpRecordChange(), NoOpUnitOfWork())

    result = await use_case.execute(
        identity=identity,
        device_group_id=group.id,
        name="Staging",
        description="  Deployment group  ",
    )

    assert repository.updated is not None
    assert result.id == group.id
    assert result.user_id == identity.user_id
    assert result.created_at == group.created_at
    assert result.updated_at > group.updated_at
    assert result.name == "Staging"
    assert result.description == "Deployment group"


@pytest.mark.anyio
async def test_update_device_group_rejects_missing_or_invalid_group() -> None:
    identity = make_identity()
    repository = FakeDeviceGroupRepository()
    use_case = UpdateDeviceGroup(repository, NoOpRecordChange(), NoOpUnitOfWork())

    with pytest.raises(DeviceGroupNotFound):
        await use_case.execute(
            identity=identity,
            device_group_id=uuid4(),
            name="Staging",
            description=None,
        )

    group = make_group(identity.user_id)
    repository.groups[group.id] = group
    with pytest.raises(InvalidInput):
        await use_case.execute(
            identity=identity,
            device_group_id=group.id,
            name="  ",
            description=None,
        )
    assert repository.updated is None


@pytest.mark.anyio
async def test_delete_device_group_deletes_owned_group_only() -> None:
    identity = make_identity()
    group = make_group(identity.user_id)
    repository = FakeDeviceGroupRepository([group])
    use_case = DeleteDeviceGroup(repository, NoOpRecordChange(), NoOpUnitOfWork())

    await use_case.execute(identity=identity, device_group_id=group.id)
    assert group.id not in repository.groups

    with pytest.raises(DeviceGroupNotFound):
        await use_case.execute(identity=identity, device_group_id=group.id)

    other_group = make_group()
    repository.groups[other_group.id] = other_group
    with pytest.raises(DeviceGroupNotFound):
        await use_case.execute(identity=identity, device_group_id=other_group.id)
    assert other_group.id in repository.groups
