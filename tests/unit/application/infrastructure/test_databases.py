from datetime import UTC, datetime
from uuid import uuid4

import pytest
from tests.support import NoOpUnitOfWork
from tests.support_databases import (
    FakeDatabaseRepository,
    RecordingDatabaseChangeRecorder,
    add_owned_database_associations,
    make_database,
    make_database_identity,
)

from app.application.common.exceptions import InvalidInput
from app.application.infrastructure.exceptions import (
    DatabaseAssociationNotFound,
    DatabaseNotFound,
    DatabaseVersionConflict,
)
from app.application.infrastructure.use_cases.database import (
    CreateDatabase,
    DeleteDatabase,
    GetDatabase,
    GetDatabasesByContainer,
    GetDatabasesByDevice,
    GetDatabasesByEnvironment,
    GetDatabasesByProject,
    GetDatabasesByService,
    GetUserDatabases,
    UpdateDatabase,
)
from app.domain.common.enums import EntityType
from app.domain.infrastructure.enums import DbmsType, ResourceStatus
from app.domain.synchronization import ChangeOperation


@pytest.mark.anyio
async def test_create_database_persists_endpoint_and_records_change() -> None:
    identity = make_database_identity()
    repository = FakeDatabaseRepository()
    recorder = RecordingDatabaseChangeRecorder()
    device_id, project_id, environment_id, container_id, service_id = (
        add_owned_database_associations(repository, identity)
    )

    result = await CreateDatabase(repository, recorder, NoOpUnitOfWork()).execute(
        identity=identity,
        device_id=device_id,
        project_id=project_id,
        environment_id=environment_id,
        container_id=container_id,
        service_id=service_id,
        name=" primary ",
        dbms_type=DbmsType.POSTGRESQL,
        host=" db.internal ",
        port=5432,
        database_name=" app ",
        metadata={"region": "local"},
    )

    assert result.name == "primary"
    assert result.host == "db.internal"
    assert result.port == 5432
    assert result.database_name == "app"
    assert result.status is ResourceStatus.UNKNOWN
    assert result.version == 1
    assert result.created_at.tzinfo is not None
    assert repository.databases[result.id].id == result.id
    event_args, _ = recorder.events[0]
    assert event_args[:5] == (
        identity,
        EntityType.DATABASE,
        result.id,
        ChangeOperation.INSERT,
        1,
    )
    assert event_args[5]["host"] == "db.internal"
    assert "metadata" not in event_args[5]


@pytest.mark.anyio
async def test_create_database_rejects_invalid_values_and_foreign_associations() -> None:
    identity = make_database_identity()
    repository = FakeDatabaseRepository()
    recorder = RecordingDatabaseChangeRecorder()
    device_id, project_id, _, _, _ = add_owned_database_associations(repository, identity)
    use_case = CreateDatabase(repository, recorder, NoOpUnitOfWork())

    with pytest.raises(InvalidInput):
        await use_case.execute(
            identity,
            device_id,
            " ",
            DbmsType.POSTGRESQL,
            port=70000,
        )

    with pytest.raises(DatabaseAssociationNotFound):
        await use_case.execute(
            identity,
            uuid4(),
            "foreign",
            DbmsType.POSTGRESQL,
            project_id=project_id,
        )

    assert repository.databases == {}
    assert recorder.events == []


@pytest.mark.anyio
async def test_database_get_and_parent_lists_are_owner_scoped() -> None:
    identity = make_database_identity()
    repository = FakeDatabaseRepository()
    device_id, project_id, environment_id, container_id, service_id = (
        add_owned_database_associations(repository, identity)
    )
    database = make_database(
        device_id, project_id, environment_id, container_id, service_id
    )
    repository.databases[database.id] = database
    other_identity = make_database_identity()

    retrieved = await GetDatabase(repository).execute(identity, database.id)
    assert retrieved.id == database.id
    assert [item.id for item in await GetUserDatabases(repository).execute(identity)] == [
        database.id
    ]
    assert [
        item.id
        for item in await GetDatabasesByDevice(repository).execute(identity, device_id)
    ] == [database.id]
    assert [
        item.id
        for item in await GetDatabasesByProject(repository).execute(identity, project_id)
    ] == [database.id]
    assert [
        item.id
        for item in await GetDatabasesByEnvironment(repository).execute(
            identity, environment_id
        )
    ] == [database.id]
    assert [
        item.id
        for item in await GetDatabasesByContainer(repository).execute(
            identity, container_id
        )
    ] == [database.id]
    assert [
        item.id
        for item in await GetDatabasesByService(repository).execute(identity, service_id)
    ] == [database.id]
    assert await GetUserDatabases(repository).execute(other_identity) == []
    assert await GetDatabasesByProject(repository).execute(other_identity, project_id) == []
    with pytest.raises(DatabaseNotFound):
        await GetDatabase(repository).execute(other_identity, database.id)


@pytest.mark.anyio
async def test_update_database_increments_version_and_reports_conflicts() -> None:
    identity = make_database_identity()
    repository = FakeDatabaseRepository()
    recorder = RecordingDatabaseChangeRecorder()
    device_id, project_id, environment_id, container_id, service_id = (
        add_owned_database_associations(repository, identity)
    )
    existing = make_database(
        device_id, project_id, environment_id, container_id, service_id
    )
    repository.databases[existing.id] = existing
    use_case = UpdateDatabase(repository, recorder, NoOpUnitOfWork())
    update_data = {
        "identity": identity,
        "database_id": existing.id,
        "expected_version": 1,
        "device_id": device_id,
        "project_id": project_id,
        "environment_id": environment_id,
        "container_id": container_id,
        "service_id": service_id,
        "name": "primary-v2",
        "dbms_type": DbmsType.POSTGRESQL,
        "status": ResourceStatus.RUNNING,
        "host": "db.internal",
        "port": 5433,
        "database_name": "app_v2",
        "last_checked_at": datetime.now(UTC),
        "metadata": {"region": "local"},
    }

    updated = await use_case.execute(**update_data)

    assert updated.version == 2
    assert updated.name == "primary-v2"
    assert updated.host == "db.internal"
    assert updated.port == 5433
    assert updated.status is ResourceStatus.RUNNING
    assert updated.created_at == existing.created_at
    assert recorder.events[-1][0][3:5] == (ChangeOperation.UPDATE, 2)

    with pytest.raises(DatabaseVersionConflict):
        await use_case.execute(**{**update_data, "expected_version": 1})
    assert len(recorder.events) == 1

    with pytest.raises(DatabaseAssociationNotFound):
        await use_case.execute(
            **{**update_data, "expected_version": 2, "device_id": uuid4()}
        )


@pytest.mark.anyio
async def test_delete_database_records_tombstone_and_reports_missing_database() -> None:
    identity = make_database_identity()
    repository = FakeDatabaseRepository()
    recorder = RecordingDatabaseChangeRecorder()
    device_id, project_id, environment_id, container_id, service_id = (
        add_owned_database_associations(repository, identity)
    )
    database = make_database(
        device_id, project_id, environment_id, container_id, service_id
    )
    repository.databases[database.id] = database
    use_case = DeleteDatabase(repository, recorder, NoOpUnitOfWork())

    await use_case.execute(identity, database.id)

    assert database.id not in repository.databases
    assert recorder.events[0][0][3:5] == (ChangeOperation.DELETE, 2)
    with pytest.raises(DatabaseNotFound):
        await use_case.execute(identity, database.id)
