from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.domain.infrastructure import (
    InvalidService,
    Service,
    ServiceName,
    SystemIdentifier,
)
from app.domain.infrastructure.enums import ResourceStatus, ServiceType


def make_service(**overrides: Any) -> Service:
    now = datetime.now(UTC)
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "device_id": uuid4(),
        "project_id": uuid4(),
        "environment_id": uuid4(),
        "name": ServiceName("api"),
        "service_type": ServiceType.APPLICATION,
        "description": "API service",
        "system_identifier": SystemIdentifier("systemd:api"),
        "status": ResourceStatus.RUNNING,
        "last_status_at": now,
        "metadata": {"port": 8080},
        "version": 2,
        "created_at": now - timedelta(minutes=1),
        "updated_at": now,
    }
    values.update(overrides)
    return Service(**values)


def test_service_accepts_value_objects_and_copies_metadata() -> None:
    service = make_service()
    metadata = service.metadata
    assert service.name == "api"
    assert service.name_value == ServiceName("api")
    assert service.system_identifier == "systemd:api"
    assert service.system_identifier_value == SystemIdentifier("systemd:api")
    assert metadata == {"port": 8080}
    assert metadata is not None
    metadata["port"] = 9000
    assert service.metadata == {"port": 8080}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entity_id", "not-a-uuid"),
        ("device_id", "not-a-uuid"),
        ("project_id", "not-a-uuid"),
        ("environment_id", "not-a-uuid"),
        ("name", "api"),
        ("system_identifier", "systemd:api"),
        ("service_type", "application"),
        ("status", "running"),
        ("metadata", ["not", "an", "object"]),
        ("version", True),
        ("created_at", datetime(2026, 1, 1)),
    ],
)
def test_service_rejects_invalid_values(field: str, value: object) -> None:
    with pytest.raises(InvalidService):
        make_service(**{field: value})


def test_service_normalizes_empty_description_and_allows_missing_links() -> None:
    service = make_service(
        project_id=None,
        environment_id=None,
        description="  ",
        system_identifier=None,
        last_status_at=None,
    )
    assert service.project_id is None
    assert service.environment_id is None
    assert service.description is None
    assert service.system_identifier is None


def test_service_rejects_inconsistent_timestamps() -> None:
    now = datetime.now(UTC)
    with pytest.raises(InvalidService):
        make_service(created_at=now, updated_at=now - timedelta(seconds=1))
    with pytest.raises(InvalidService):
        make_service(
            created_at=now, updated_at=now, last_status_at=now - timedelta(seconds=1)
        )


@pytest.mark.parametrize("name", ["  ", "x" * 256])
def test_service_name_rejects_invalid_values(name: str) -> None:
    with pytest.raises(InvalidService):
        ServiceName(name)


@pytest.mark.parametrize("identifier", ["  ", "x" * 513])
def test_system_identifier_rejects_invalid_values(identifier: str) -> None:
    with pytest.raises(InvalidService):
        SystemIdentifier(identifier)
