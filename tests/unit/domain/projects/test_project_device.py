from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.domain.projects.entities.project_device import ProjectDevice
from app.domain.projects.exceptions import InvalidProjectDeviceRelation


def make_project_device(**overrides: Any) -> ProjectDevice:
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "project_id": uuid4(),
        "device_id": uuid4(),
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
        "role": "  deployer  ",
    }
    values.update(overrides)
    return ProjectDevice(**values)


def test_project_device_normalizes_role_and_exposes_values() -> None:
    relation = make_project_device()

    assert relation.role == "deployer"
    assert relation.created_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_project_device_converts_blank_role_to_none() -> None:
    assert make_project_device(role="   ").role is None


def test_project_device_rejects_role_over_maximum_length() -> None:
    with pytest.raises(InvalidProjectDeviceRelation):
        make_project_device(role="x" * 101)


def test_project_device_rejects_naive_creation_time() -> None:
    with pytest.raises(InvalidProjectDeviceRelation):
        make_project_device(created_at=datetime(2026, 1, 1))
