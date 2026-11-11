from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpUnitOfWork

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import (
    ContainerNotFound,
    DeviceNotFound,
    ServiceNotFound,
)
from app.application.monitoring import CreateLogMetadata, GetUserLogMetadata
from app.application.projects.exceptions import ProjectNotFound
from app.domain.identity import EmailAddress, TokenHash
from app.domain.monitoring import LogMetadata


class ObjectRepositoryStub:
    def __init__(self, objects: dict[UUID, object]) -> None:
        self.objects = objects

    async def get_by_id(self, *_args):
        return self.objects.get(_args[-1])


class LogMetadataRepositoryStub:
    def __init__(self) -> None:
        self.values: list[LogMetadata] = []

    async def create(self, value: LogMetadata) -> None:
        self.values.append(value)

    async def get_user_log_metadata(
        self,
        user_id,
        project_id,
        device_id,
        service_id,
        container_id,
        source,
        severity,
        start,
        end,
        limit,
        offset,
    ):
        values = [value for value in self.values if value.user_id == user_id]
        for field, expected in (
            ("project_id", project_id),
            ("device_id", device_id),
            ("service_id", service_id),
            ("container_id", container_id),
            ("source", source),
            ("severity", severity),
        ):
            if expected is not None:
                values = [value for value in values if getattr(value, field) == expected]
        if start is not None:
            values = [
                value
                for value in values
                if value.collected_at is not None and value.collected_at >= start
            ]
        if end is not None:
            values = [
                value
                for value in values
                if value.collected_at is not None and value.collected_at < end
            ]
        return sorted(
            values,
            key=lambda value: value.collected_at or value.created_at,
            reverse=True,
        )[offset : offset + limit]


def make_identity() -> VerifiedIdentity:
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="log-metadata-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_create_use_case(
    *,
    project_id: UUID | None = None,
    device_id: UUID | None = None,
    service_id: UUID | None = None,
    container_id: UUID | None = None,
):
    projects = ObjectRepositoryStub(
        {project_id: SimpleNamespace(id=project_id)} if project_id else {}
    )
    devices = ObjectRepositoryStub(
        {device_id: SimpleNamespace(id=device_id)} if device_id else {}
    )
    services = ObjectRepositoryStub(
        {
            service_id: SimpleNamespace(
                id=service_id, device_id=device_id, project_id=project_id
            )
        }
        if service_id
        else {}
    )
    containers = ObjectRepositoryStub(
        {
            container_id: SimpleNamespace(
                id=container_id,
                device_id=device_id,
                service_id=service_id,
                project_id=project_id,
            )
        }
        if container_id
        else {}
    )
    repository = LogMetadataRepositoryStub()
    use_case = CreateLogMetadata(
        repository,
        projects,
        devices,
        services,
        containers,
        NoOpUnitOfWork(),
    )
    return repository, use_case


@pytest.mark.anyio
async def test_create_and_filter_log_metadata_without_raw_log_contents() -> None:
    identity = make_identity()
    project_id, device_id, service_id, container_id = (
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
    )
    repository, create = make_create_use_case(
        project_id=project_id,
        device_id=device_id,
        service_id=service_id,
        container_id=container_id,
    )
    collected_at = datetime(2026, 2, 1, tzinfo=UTC)
    result = await create.create_log_metadata(
        identity,
        "application",
        project_id,
        device_id,
        service_id,
        container_id,
        "logs/2026-02-01",
        "Rotated log file",
        "info",
        42,
        collected_at,
    )

    values = await GetUserLogMetadata(repository).get_user_log_metadata(
        identity,
        project_id,
        device_id,
        service_id,
        container_id,
        "application",
        "info",
        collected_at,
        collected_at + timedelta(hours=1),
        100,
        0,
    )

    assert result.user_id == identity.user_id
    assert result.records_count == 42
    assert len(values) == 1
    assert values[0].description == "Rotated log file"
    assert not hasattr(values[0], "raw_log")


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("field", "error"),
    [
        ("project_id", ProjectNotFound),
        ("device_id", DeviceNotFound),
        ("service_id", ServiceNotFound),
        ("container_id", ContainerNotFound),
    ],
)
async def test_create_log_metadata_rejects_unowned_associations(field, error) -> None:
    identity = make_identity()
    _, create = make_create_use_case()
    fields = {
        "project_id": None,
        "device_id": None,
        "service_id": None,
        "container_id": None,
    }
    fields[field] = uuid4()

    with pytest.raises(error):
        await create.create_log_metadata(
            identity,
            "agent",
            fields["project_id"],
            fields["device_id"],
            fields["service_id"],
            fields["container_id"],
            None,
            None,
            None,
            None,
            None,
        )


@pytest.mark.anyio
async def test_create_log_metadata_rejects_mismatched_service_device() -> None:
    identity = make_identity()
    device_id = uuid4()
    other_device_id = uuid4()
    project_id, service_id = uuid4(), uuid4()
    projects = ObjectRepositoryStub({project_id: SimpleNamespace(id=project_id)})
    devices = ObjectRepositoryStub({device_id: SimpleNamespace(id=device_id)})
    services = ObjectRepositoryStub(
        {
            service_id: SimpleNamespace(
                id=service_id, device_id=other_device_id, project_id=project_id
            )
        }
    )
    repository = LogMetadataRepositoryStub()
    create = CreateLogMetadata(
        repository,
        projects,
        devices,
        services,
        ObjectRepositoryStub({}),
        NoOpUnitOfWork(),
    )

    with pytest.raises(InvalidInput, match="Service does not belong"):
        await create.create_log_metadata(
            identity,
            "agent",
            project_id,
            device_id,
            service_id,
            None,
            None,
            None,
            None,
            None,
            None,
        )
