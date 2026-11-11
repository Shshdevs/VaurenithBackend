from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpUnitOfWork
from tests.support_connections import (
    FakeConnectionRepository,
    make_connection_identity,
)

from app.application.common.exceptions import InvalidInput
from app.application.infrastructure.exceptions import (
    ConnectionDeviceNotFound,
    ConnectionNotFound,
    ConnectionVersionConflict,
    DefaultConnectionConflict,
)
from app.application.infrastructure.use_cases.connection import (
    CreateConnection,
    DeleteConnection,
    GetConnection,
    GetDeviceConnections,
    GetUserConnections,
    ReportConnectionStatus,
    UpdateConnection,
)
from app.domain.common.enums import EntityType
from app.domain.infrastructure.enums import AuthenticationType, ConnectionStatus
from app.domain.synchronization.enums import ChangeOperation


class RecordingChangeRecorder:
    def __init__(self) -> None:
        self.events: list[tuple[EntityType, UUID, ChangeOperation, int, object]] = []

    async def execute(
        self,
        identity,
        entity_type: EntityType,
        entity_id: UUID,
        operation: ChangeOperation,
        version: int,
        payload=None,
    ) -> None:
        self.events.append((entity_type, entity_id, operation, version, payload))


def build_connection_use_cases(repository: FakeConnectionRepository):
    recorder = RecordingChangeRecorder()
    unit_of_work = NoOpUnitOfWork()
    return (
        CreateConnection(repository, recorder, unit_of_work),
        UpdateConnection(repository, recorder, unit_of_work),
        DeleteConnection(repository, recorder, unit_of_work),
        ReportConnectionStatus(repository, recorder, unit_of_work),
        recorder,
    )


@pytest.mark.anyio
async def test_connection_crud_status_and_change_log() -> None:
    identity = make_connection_identity()
    device_id = uuid4()
    repository = FakeConnectionRepository({device_id: identity.user_id})
    create, update, delete, report_status, recorder = build_connection_use_cases(repository)

    created = await create.execute(
        identity,
        device_id,
        " Primary SSH ",
        " server.example.test ",
        " admin ",
        AuthenticationType.SSH_KEY,
        is_default=True,
    )

    assert created.name == "Primary SSH"
    assert created.host == "server.example.test"
    assert created.username == "admin"
    assert created.version == 1
    assert created.is_default
    assert recorder.events[0][:4] == (
        EntityType.CONNECTION,
        created.id,
        ChangeOperation.INSERT,
        1,
    )
    assert "last_error" not in recorder.events[0][4]

    fetched = await GetConnection(repository).execute(identity, created.id)
    by_user = await GetUserConnections(repository).execute(identity)
    by_device = await GetDeviceConnections(repository).execute(identity, device_id)
    assert fetched.id == created.id
    assert [item.id for item in by_user] == [created.id]
    assert [item.id for item in by_device] == [created.id]

    updated = await update.execute(
        identity,
        created.id,
        1,
        "Primary production SSH",
        "ssh.example.test",
        "deploy",
        AuthenticationType.AGENT,
        port=2222,
        connection_timeout=45,
        is_default=True,
    )
    assert updated.version == 2
    assert updated.port == 2222
    assert recorder.events[-1][2:4] == (ChangeOperation.UPDATE, 2)

    with pytest.raises(ConnectionVersionConflict):
        await update.execute(
            identity,
            created.id,
            1,
            "Primary production SSH",
            "ssh.example.test",
            "deploy",
            AuthenticationType.AGENT,
        )

    connected_at = datetime.now(UTC)
    reported = await report_status.execute(
        identity,
        created.id,
        2,
        ConnectionStatus.CONNECTED,
        last_error="credential text must not be returned",
        last_connected_at=connected_at,
    )
    assert reported.version == 3
    assert reported.last_status == ConnectionStatus.CONNECTED.value
    assert reported.last_connected_at == connected_at
    assert not hasattr(reported, "last_error")
    assert recorder.events[-1][4] == {
        "last_status": "connected",
        "last_connected_at": connected_at.isoformat(),
    }

    await delete.execute(identity, created.id)
    assert await GetUserConnections(repository).execute(identity) == []
    assert recorder.events[-1][2:4] == (ChangeOperation.DELETE, 4)


@pytest.mark.anyio
async def test_connection_rejects_invalid_input_and_foreign_device() -> None:
    identity = make_connection_identity()
    foreign_identity = make_connection_identity()
    device_id = uuid4()
    repository = FakeConnectionRepository({device_id: identity.user_id})
    create, _, _, _, _ = build_connection_use_cases(repository)

    with pytest.raises(InvalidInput):
        await create.execute(
            identity,
            device_id,
            " ",
            "server.example.test",
            "admin",
            AuthenticationType.PASSWORD,
        )

    with pytest.raises(ConnectionDeviceNotFound):
        await create.execute(
            foreign_identity,
            device_id,
            "Private server",
            "server.example.test",
            "admin",
            AuthenticationType.PASSWORD,
        )

    with pytest.raises(ConnectionNotFound):
        await GetConnection(repository).execute(foreign_identity, uuid4())

    assert repository.connections == {}


@pytest.mark.anyio
async def test_only_one_default_connection_is_allowed_per_device() -> None:
    identity = make_connection_identity()
    device_id = uuid4()
    repository = FakeConnectionRepository({device_id: identity.user_id})
    create, _, _, _, _ = build_connection_use_cases(repository)
    await create.execute(
        identity,
        device_id,
        "Primary",
        "server-a.example.test",
        "admin",
        AuthenticationType.SSH_KEY,
        is_default=True,
    )

    with pytest.raises(DefaultConnectionConflict):
        await create.execute(
            identity,
            device_id,
            "Second default",
            "server-b.example.test",
            "admin",
            AuthenticationType.SSH_KEY,
            is_default=True,
        )

    assert len(repository.connections) == 1
