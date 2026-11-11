from datetime import UTC, datetime
from uuid import uuid4

import pytest
from tests.support import NoOpUnitOfWork
from tests.support_containers import (
    FakeContainerRepository,
    RecordingChangeRecorder,
    add_owned_container_associations,
    make_container,
    make_container_identity,
)

from app.application.common.exceptions import InvalidInput
from app.application.infrastructure.exceptions import (
    ContainerAssociationNotFound,
    ContainerNotFound,
    ContainerVersionConflict,
)
from app.application.infrastructure.use_cases.container import (
    CreateContainer,
    DeleteContainer,
    GetContainer,
    GetContainersByProject,
    GetDeviceContainers,
    GetEnvironmentContainers,
    GetServiceContainers,
    GetUserContainers,
    UpdateContainer,
)
from app.domain.common.enums import EntityType
from app.domain.infrastructure.enums import ContainerStatus
from app.domain.synchronization import ChangeOperation


@pytest.mark.anyio
async def test_create_container_persists_defaults_and_records_change() -> None:
    identity = make_container_identity()
    repository = FakeContainerRepository()
    recorder = RecordingChangeRecorder()
    device_id, project_id, environment_id, service_id = add_owned_container_associations(
        repository, identity
    )

    result = await CreateContainer(repository, recorder, NoOpUnitOfWork()).execute(
        identity=identity,
        device_id=device_id,
        project_id=project_id,
        environment_id=environment_id,
        service_id=service_id,
        container_runtime_id=" docker:api-123 ",
        name=" api ",
        image=" example/api:1.0 ",
        ports={"8080/tcp": [8080]},
    )

    assert result.name == "api"
    assert result.container_runtime_id == "docker:api-123"
    assert result.image == "example/api:1.0"
    assert result.status is ContainerStatus.UNKNOWN
    assert result.version == 1
    assert result.created_at.tzinfo is not None
    assert repository.containers[result.id].id == result.id
    assert len(recorder.events) == 1
    event_args, _ = recorder.events[0]
    assert event_args[:5] == (
        identity,
        EntityType.CONTAINER,
        result.id,
        ChangeOperation.INSERT,
        1,
    )
    assert event_args[5]["service_id"] == str(service_id)


@pytest.mark.anyio
async def test_create_container_rejects_invalid_values_and_foreign_associations() -> None:
    identity = make_container_identity()
    repository = FakeContainerRepository()
    recorder = RecordingChangeRecorder()
    device_id, project_id, _, _ = add_owned_container_associations(repository, identity)
    use_case = CreateContainer(repository, recorder, NoOpUnitOfWork())

    with pytest.raises(InvalidInput):
        await use_case.execute(
            identity=identity,
            device_id=device_id,
            container_runtime_id=" ",
            name="api",
        )

    with pytest.raises(ContainerAssociationNotFound):
        await use_case.execute(
            identity=identity,
            device_id=uuid4(),
            project_id=project_id,
            container_runtime_id="docker:foreign",
            name="foreign",
        )

    assert repository.containers == {}
    assert recorder.events == []


@pytest.mark.anyio
async def test_container_get_and_parent_lists_are_owner_scoped() -> None:
    identity = make_container_identity()
    repository = FakeContainerRepository()
    device_id, project_id, environment_id, service_id = add_owned_container_associations(
        repository, identity
    )
    container = make_container(device_id, project_id, environment_id, service_id)
    repository.containers[container.id] = container
    other_identity = make_container_identity()

    retrieved = await GetContainer(repository).execute(identity, container.id)
    assert retrieved.id == container.id
    assert [item.id for item in await GetUserContainers(repository).execute(identity)] == [
        container.id
    ]
    assert [
        item.id
        for item in await GetDeviceContainers(repository).execute(identity, device_id)
    ] == [container.id]
    assert [
        item.id
        for item in await GetContainersByProject(repository).execute(identity, project_id)
    ] == [container.id]
    assert [
        item.id
        for item in await GetEnvironmentContainers(repository).execute(
            identity, environment_id
        )
    ] == [container.id]
    assert [
        item.id
        for item in await GetServiceContainers(repository).execute(identity, service_id)
    ] == [container.id]

    assert await GetUserContainers(repository).execute(other_identity) == []
    assert await GetDeviceContainers(repository).execute(other_identity, device_id) == []
    assert (
        await GetContainersByProject(repository).execute(other_identity, project_id) == []
    )
    with pytest.raises(ContainerNotFound):
        await GetContainer(repository).execute(other_identity, container.id)


@pytest.mark.anyio
async def test_update_container_increments_version_and_reports_conflicts() -> None:
    identity = make_container_identity()
    repository = FakeContainerRepository()
    recorder = RecordingChangeRecorder()
    device_id, project_id, environment_id, service_id = add_owned_container_associations(
        repository, identity
    )
    existing = make_container(device_id, project_id, environment_id, service_id)
    repository.containers[existing.id] = existing
    use_case = UpdateContainer(repository, recorder, NoOpUnitOfWork())
    update_data = {
        "identity": identity,
        "container_id": existing.id,
        "expected_version": 1,
        "device_id": device_id,
        "project_id": project_id,
        "environment_id": environment_id,
        "service_id": service_id,
        "container_runtime_id": "docker:api-123",
        "name": "api-v2",
        "status": ContainerStatus.RUNNING,
        "image": "example/api:2.0",
        "ports": {"8080/tcp": [8080]},
        "started_at": datetime.now(UTC),
    }

    updated = await use_case.execute(**update_data)

    assert updated.version == 2
    assert updated.name == "api-v2"
    assert updated.status is ContainerStatus.RUNNING
    assert updated.created_at == existing.created_at
    assert repository.containers[existing.id].version == 2
    assert recorder.events[-1][0][3:5] == (ChangeOperation.UPDATE, 2)

    with pytest.raises(ContainerVersionConflict):
        await use_case.execute(**{**update_data, "expected_version": 1})
    assert len(recorder.events) == 1

    with pytest.raises(ContainerAssociationNotFound):
        await use_case.execute(
            **{**update_data, "expected_version": 2, "device_id": uuid4()}
        )


@pytest.mark.anyio
async def test_delete_container_records_tombstone_and_hides_missing_resources() -> None:
    identity = make_container_identity()
    repository = FakeContainerRepository()
    recorder = RecordingChangeRecorder()
    device_id, project_id, environment_id, service_id = add_owned_container_associations(
        repository, identity
    )
    container = make_container(device_id, project_id, environment_id, service_id)
    repository.containers[container.id] = container

    await DeleteContainer(repository, recorder, NoOpUnitOfWork()).execute(
        identity, container.id
    )

    assert container.id not in repository.containers
    assert recorder.events[0][0][3:5] == (ChangeOperation.DELETE, 2)
    with pytest.raises(ContainerNotFound):
        await DeleteContainer(repository, recorder, NoOpUnitOfWork()).execute(
            identity, container.id
        )
