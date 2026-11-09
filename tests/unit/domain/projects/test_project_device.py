from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.domain.projects.entities.project_device import ProjectDevice
from app.domain.projects.exceptions import InvalidProjectDevice
from app.domain.projects.value_objects import ProjectDeviceRole


def make_project_device(**overrides: Any) -> ProjectDevice:
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "project_id": uuid4(),
        "device_id": uuid4(),
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "role": ProjectDeviceRole("  deployer  "),
    }
    values.update(overrides)
    return ProjectDevice(**values)


def test_project_device_normalizes_role_and_exposes_values() -> None:
    relation = make_project_device()

    assert relation.role == "deployer"
    assert relation.created_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_project_device_role_value_object_normalizes_and_validates_role() -> None:
    role = ProjectDeviceRole("  deployer  ")

    assert role.value == "deployer"
    with pytest.raises(InvalidProjectDevice):
        ProjectDeviceRole("   ")
    with pytest.raises(InvalidProjectDevice):
        ProjectDeviceRole("x" * 101)


def test_project_device_rejects_naive_creation_time() -> None:
    with pytest.raises(InvalidProjectDevice):
        make_project_device(created_at=datetime(2026, 1, 1))
