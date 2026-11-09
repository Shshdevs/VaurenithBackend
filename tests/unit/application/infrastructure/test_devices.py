from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpRecordChange

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceNotFound, DeviceVersionConflict
from app.application.infrastructure.use_cases.device import (
    CreateDevice,
    DeleteDevice,
    GetDevice,
    GetUserDevices,
    UpdateDevice,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import Device, DeviceName, OperatingSystem
from app.domain.infrastructure.enums import DeviceType


class FakeDeviceRepository:
    def __init__(self) -> None:
        self.devices: dict[UUID, Device] = {}
        self.deleted: set[UUID] = set()
        self.created: Device | None = None
        self.updated: Device | None = None

    async def get_by_id(self, identity: VerifiedIdentity, device_id: UUID) -> Device | None:
        device = self.devices.get(device_id)
        if (
            device is None
            or device_id in self.deleted
            or device.user_id != identity.user_id
        ):
            return None
        return device

    async def get_by_user(self, identity: VerifiedIdentity) -> list[Device]:
        return [
            device
            for device_id, device in self.devices.items()
            if device.user_id == identity.user_id and device_id not in self.deleted
        ]

    async def create(self, device: Device) -> None:
        self.created = device
        self.devices[device.id] = device

    async def update(
        self, identity: VerifiedIdentity, device: Device, expected_version: int
    ) -> bool:
        existing = await self.get_by_id(identity, device.id)
        if existing is None or existing.version != expected_version:
            return False
        self.updated = device
        self.devices[device.id] = device
        return True

    async def delete(
        self, identity: VerifiedIdentity, device_id: UUID, deleted_at: datetime
    ) -> bool:
        if await self.get_by_id(identity, device_id) is None:
            return False
        self.deleted.add(device_id)
        return True


def make_identity(user_id: UUID | None = None) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id or uuid4(),
        email=EmailAddress("device-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_device(user_id: UUID) -> Device:
    now = datetime.now(UTC)
    return Device(
        entity_id=uuid4(),
        user_id=user_id,
        name=DeviceName("worker-01"),
        created_at=now,
        updated_at=now,
        device_type=DeviceType.VPS,
        operating_system_info=OperatingSystem("Linux", "6.1", "x86_64"),
    )


@pytest.mark.anyio
async def test_create_device_binds_owner_and_normalizes_fields() -> None:
    identity = make_identity()
    repository = FakeDeviceRepository()
    result = await CreateDevice(repository, NoOpRecordChange()).execute(
        identity=identity,
        name=" worker-01 ",
        device_type=DeviceType.VPS,
        operating_system=" Linux ",
        os_version=" 6.1 ",
        architecture=" x86_64 ",
        tags=[" production "],
    )
    assert repository.created is not None
    assert repository.created.user_id == identity.user_id
    assert result.user_id == identity.user_id
    assert result.name == "worker-01"
    assert result.operating_system == "Linux"
    assert result.tags == ["production"]


@pytest.mark.anyio
async def test_create_device_rejects_invalid_values() -> None:
    repository = FakeDeviceRepository()
    with pytest.raises(InvalidInput):
        await CreateDevice(repository, NoOpRecordChange()).execute(
            identity=make_identity(), name="  ", device_type=DeviceType.VPS
        )
    with pytest.raises(InvalidInput):
        await CreateDevice(repository, NoOpRecordChange()).execute(
            identity=make_identity(),
            name="worker",
            device_type=DeviceType.VPS,
            tags=["  "],
        )
    assert repository.created is None


@pytest.mark.anyio
async def test_get_and_list_devices_are_owner_scoped() -> None:
    identity = make_identity()
    own_device = make_device(identity.user_id)
    other_device = make_device(uuid4())
    repository = FakeDeviceRepository()
    repository.devices = {own_device.id: own_device, other_device.id: other_device}

    fetched = await GetDevice(repository).execute(identity, own_device.id)
    assert fetched.id == own_device.id
    assert [item.id for item in await GetUserDevices(repository).execute(identity)] == [
        own_device.id
    ]
    with pytest.raises(DeviceNotFound):
        await GetDevice(repository).execute(identity, other_device.id)


@pytest.mark.anyio
async def test_update_preserves_identity_timestamps_and_increments_version() -> None:
    identity = make_identity()
    existing = make_device(identity.user_id)
    repository = FakeDeviceRepository()
    repository.devices[existing.id] = existing

    updated = await UpdateDevice(repository, NoOpRecordChange()).execute(
        identity=identity,
        device_id=existing.id,
        expected_version=existing.version,
        name="worker-02",
        device_type=DeviceType.CLOUD,
        tags=[" staging "],
    )

    assert updated.id == existing.id
    assert updated.user_id == identity.user_id
    assert updated.created_at == existing.created_at
    assert updated.updated_at > existing.updated_at
    assert updated.version == existing.version + 1
    assert updated.name == "worker-02"
    assert updated.operating_system is None

    with pytest.raises(DeviceVersionConflict):
        await UpdateDevice(repository, NoOpRecordChange()).execute(
            identity=identity,
            device_id=existing.id,
            expected_version=existing.version,
            name="stale-name",
            device_type=DeviceType.VPS,
        )


@pytest.mark.anyio
async def test_update_rejects_missing_or_invalid_device() -> None:
    identity = make_identity()
    repository = FakeDeviceRepository()
    use_case = UpdateDevice(repository, NoOpRecordChange())
    with pytest.raises(DeviceNotFound):
        await use_case.execute(
            identity=identity,
            device_id=uuid4(),
            expected_version=1,
            name="worker",
            device_type=DeviceType.VPS,
        )

    device = make_device(identity.user_id)
    repository.devices[device.id] = device
    with pytest.raises(InvalidInput):
        await use_case.execute(
            identity=identity,
            device_id=device.id,
            expected_version=device.version,
            name="worker",
            device_type=DeviceType.VPS,
            architecture="x" * 51,
        )
    assert repository.updated is None


@pytest.mark.anyio
async def test_delete_hides_device_and_rejects_other_owners() -> None:
    identity = make_identity()
    device = make_device(identity.user_id)
    repository = FakeDeviceRepository()
    repository.devices[device.id] = device
    use_case = DeleteDevice(repository, NoOpRecordChange())

    await use_case.execute(identity, device.id)
    assert await GetUserDevices(repository).execute(identity) == []
    with pytest.raises(DeviceNotFound):
        await GetDevice(repository).execute(identity, device.id)
    with pytest.raises(DeviceNotFound):
        await use_case.execute(make_identity(), device.id)
