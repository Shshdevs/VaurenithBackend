from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.domain.projects.entities.project import Project
from app.domain.projects.enums import ProjectStatus, ProjectType
from app.domain.projects.exceptions import InvalidProject
from app.domain.projects.value_objects import ProjectName


def make_project(**overrides: Any) -> Project:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "user_id": uuid4(),
        "name": ProjectName("  Project alpha  "),
        "created_at": created_at,
        "updated_at": created_at,
    }
    values.update(overrides)
    if isinstance(values["name"], str):
        values["name"] = ProjectName(values["name"])
    return Project(**values)


def test_project_normalizes_name_and_exposes_values() -> None:
    project = make_project(description="Description", metadata={"key": "value"})

    assert project.name == "Project alpha"
    assert project.description == "Description"
    assert project.project_type is ProjectType.OTHER
    assert project.status is ProjectStatus.ACTIVE
    assert project.version == 1
    assert project.metadata == {"key": "value"}


def test_project_metadata_is_defensively_copied() -> None:
    metadata = {"nested": {"value": 1}}
    project = make_project(metadata=metadata)
    metadata["nested"]["value"] = 2

    assert project.metadata == {"nested": {"value": 1}}

    returned_metadata = project.metadata
    assert returned_metadata is not None
    returned_metadata["nested"]["value"] = 3

    assert project.metadata == {"nested": {"value": 1}}


@pytest.mark.parametrize("name", ["", "   ", "x" * 256])
def test_project_rejects_invalid_name(name: str) -> None:
    with pytest.raises(InvalidProject):
        make_project(name=name)


def test_project_rejects_update_before_creation() -> None:
    created_at = datetime(2026, 1, 2, tzinfo=UTC)

    with pytest.raises(InvalidProject):
        make_project(created_at=created_at, updated_at=created_at - timedelta(seconds=1))


def test_project_rejects_deletion_before_creation() -> None:
    created_at = datetime(2026, 1, 2, tzinfo=UTC)

    with pytest.raises(InvalidProject):
        make_project(
            created_at=created_at,
            updated_at=created_at,
            deleted_at=created_at - timedelta(seconds=1),
        )
