from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpUnitOfWork

from app.application.identity.dto import VerifiedIdentity
from app.application.identity.exceptions import (
    ClientDeviceConflict,
    ClientDeviceNotFound,
    SessionTokenConflict,
)
from app.application.identity.use_cases import (
    CreateDeviceSession,
    RegisterClientDevice,
    RevokeClientDevice,
    SetClientDeviceStatus,
)
from app.domain.identity import (
    ClientDevice,
    ClientDeviceStatus,
    EmailAddress,
    PlatformType,
    Session,
    TokenHash,
    User,
)


class FakeUserRepository:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def get_by_id(self, _user_id: UUID) -> User | None:
        return self.user


class FakeClientDeviceRepository:
    def __init__(self) -> None:
        self.devices: dict[UUID, ClientDevice] = {}

    async def create(self, device: ClientDevice) -> None:
        self.devices[device.id] = device

    async def get_owned(
        self, user_id: UUID, device_id: UUID, for_update: bool = False
    ) -> ClientDevice | None:
        device = self.devices.get(device_id)
        return device if device is not None and device.user_id == user_id else None

    async def list_by_user(self, user_id: UUID) -> list[ClientDevice]:
        return [device for device in self.devices.values() if device.user_id == user_id]

    async def save(self, device: ClientDevice) -> None:
        self.devices[device.id] = device


class FakeSessionRepository:
    def __init__(self) -> None:
        self.sessions: dict[str, Session] = {}

    async def has_token_hash(self, token_hash: TokenHash) -> bool:
        return token_hash.value in self.sessions

    async def create(self, session: Session) -> None:
        self.sessions[session.token_hash.value] = session

    async def revoke_device_sessions(
        self, user_id: UUID, client_device_id: UUID, at: datetime
    ) -> int:
        active = [
            session
            for session in self.sessions.values()
            if session.user_id == user_id
            and session.client_device_id == client_device_id
            and session.is_active(at)
        ]
        for session in active:
            session.revoke(at)
        return len(active)

    async def list_device_sessions(
        self, user_id: UUID, client_device_id: UUID
    ) -> list[Session]:
        return [
            session
            for session in self.sessions.values()
            if session.user_id == user_id and session.client_device_id == client_device_id
        ]


def make_identity(
    user_id: UUID | None = None, token_hash: str | None = None
) -> VerifiedIdentity:
    now = datetime.now(UTC)
    return VerifiedIdentity(
        user_id=user_id or uuid4(),
        email=EmailAddress("owner@example.test"),
        auth_provider="test-provider",
        expires_at=now + timedelta(hours=1),
        token_hash=TokenHash(token_hash or uuid4().hex * 2),
    )


def make_user(user_id: UUID) -> User:
    now = datetime.now(UTC)
    return User(
        entity_id=user_id,
        email=EmailAddress("owner@example.test"),
        display_name="Owner",
        auth_provider="test-provider",
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
async def test_register_device_creates_device_and_linked_session() -> None:
    identity = make_identity()
    users = FakeUserRepository(make_user(identity.user_id))
    devices = FakeClientDeviceRepository()
    sessions = FakeSessionRepository()
    use_case = RegisterClientDevice(users, devices, sessions, NoOpUnitOfWork())

    result = await use_case.execute(identity, "Laptop", PlatformType.MACOS, "1.0")

    device = devices.devices[result.id]
    session = sessions.sessions[identity.token_hash.value]
    assert device.user_id == identity.user_id
    assert device.status is ClientDeviceStatus.ACTIVE
    assert session.client_device_id == device.id
    assert session.user_id == identity.user_id


@pytest.mark.anyio
async def test_register_device_rejects_previously_registered_token_hash() -> None:
    identity = make_identity()
    users = FakeUserRepository(make_user(identity.user_id))
    devices = FakeClientDeviceRepository()
    sessions = FakeSessionRepository()
    existing_device = ClientDevice(
        entity_id=uuid4(),
        user_id=identity.user_id,
        name="Existing",
        platform=PlatformType.OTHER,
        registered_at=datetime.now(UTC),
    )
    await devices.create(existing_device)
    existing_session = Session(
        entity_id=uuid4(),
        user_id=identity.user_id,
        client_device_id=existing_device.id,
        token_hash=identity.token_hash,
        expires_at=identity.expires_at,
        created_at=datetime.now(UTC),
    )
    await sessions.create(existing_session)
    use_case = RegisterClientDevice(users, devices, sessions, NoOpUnitOfWork())

    with pytest.raises(ClientDeviceConflict):
        await use_case.execute(identity, "New", PlatformType.OTHER, None)


@pytest.mark.anyio
async def test_new_session_requires_owned_active_device_and_unused_token() -> None:
    identity = make_identity()
    devices = FakeClientDeviceRepository()
    sessions = FakeSessionRepository()
    device = ClientDevice(
        entity_id=uuid4(),
        user_id=identity.user_id,
        name="Laptop",
        platform=PlatformType.MACOS,
        registered_at=datetime.now(UTC),
    )
    await devices.create(device)
    use_case = CreateDeviceSession(devices, sessions, NoOpUnitOfWork())

    result = await use_case.execute(identity, device.id)

    assert result.client_device_id == device.id
    assert result.id == sessions.sessions[identity.token_hash.value].id
    with pytest.raises(SessionTokenConflict):
        await use_case.execute(identity, device.id)

    another_identity = make_identity(user_id=uuid4())
    with pytest.raises(ClientDeviceNotFound):
        await use_case.execute(another_identity, device.id)


@pytest.mark.anyio
async def test_inactive_device_revokes_sessions_without_reactivating_them() -> None:
    identity = make_identity()
    devices = FakeClientDeviceRepository()
    sessions = FakeSessionRepository()
    device = ClientDevice(
        entity_id=uuid4(),
        user_id=identity.user_id,
        name="Laptop",
        platform=PlatformType.MACOS,
        registered_at=datetime.now(UTC),
    )
    await devices.create(device)
    session = Session(
        entity_id=uuid4(),
        user_id=identity.user_id,
        client_device_id=device.id,
        token_hash=identity.token_hash,
        expires_at=identity.expires_at,
        created_at=datetime.now(UTC),
    )
    await sessions.create(session)
    use_case = SetClientDeviceStatus(devices, sessions, NoOpUnitOfWork())

    await use_case.execute(identity, device.id, ClientDeviceStatus.INACTIVE)
    assert device.status is ClientDeviceStatus.INACTIVE
    assert session.revoked_at is not None

    await use_case.execute(identity, device.id, ClientDeviceStatus.ACTIVE)
    assert device.status is ClientDeviceStatus.ACTIVE
    assert session.revoked_at is not None


@pytest.mark.anyio
async def test_revoke_device_is_terminal_and_owner_scoped() -> None:
    identity = make_identity()
    devices = FakeClientDeviceRepository()
    sessions = FakeSessionRepository()
    device = ClientDevice(
        entity_id=uuid4(),
        user_id=identity.user_id,
        name="Laptop",
        platform=PlatformType.MACOS,
        registered_at=datetime.now(UTC),
    )
    await devices.create(device)
    use_case = RevokeClientDevice(devices, sessions, NoOpUnitOfWork())

    await use_case.execute(identity, device.id)
    assert device.status is ClientDeviceStatus.REVOKED
    with pytest.raises(ClientDeviceNotFound):
        await use_case.execute(make_identity(), device.id)
    with pytest.raises(ClientDeviceConflict):
        await SetClientDeviceStatus(devices, sessions, NoOpUnitOfWork()).execute(
            identity, device.id, ClientDeviceStatus.ACTIVE
        )
