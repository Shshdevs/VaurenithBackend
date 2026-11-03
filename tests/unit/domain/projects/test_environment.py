from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.domain.projects.entities.environment import Environment
from app.domain.projects.enums import EnvironmentType
from app.domain.projects.exceptions import InvalidEnvironment


def make_environment(**overrides: Any) -> Environment:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "project_id": uuid4(),
        "name": "  Production  ",
        "environment_type": EnvironmentType.PRODUCTION,
        "description": None,
        "configuration": None,
        "created_at": created_at,
        "updated_at": created_at,
    }
    values.update(overrides)
    return Environment(**values)


def test_environment_normalizes_name_and_exposes_values() -> None:
    environment = make_environment(configuration={"region": "eu"})

    assert environment.name == "Production"
    assert environment.environment_type is EnvironmentType.PRODUCTION
    assert environment.configuration == {"region": "eu"}
    assert environment.version == 1
    assert environment.deleted_at is None


def test_environment_configuration_is_defensively_copied() -> None:
    configuration = {"nested": {"region": "eu"}}
    environment = make_environment(configuration=configuration)
    configuration["nested"]["region"] = "us"

    assert environment.configuration == {"nested": {"region": "eu"}}

    returned_configuration = environment.configuration
    assert returned_configuration is not None
    returned_configuration["nested"]["region"] = "apac"

    assert environment.configuration == {"nested": {"region": "eu"}}


@pytest.mark.parametrize("name", ["", "   ", "x" * 256])
def test_environment_rejects_invalid_name(name: str) -> None:
    with pytest.raises(InvalidEnvironment):
        make_environment(name=name)


def test_environment_rejects_update_before_creation() -> None:
    created_at = datetime(2026, 1, 2, tzinfo=UTC)

    with pytest.raises(InvalidEnvironment):
        make_environment(
            created_at=created_at, updated_at=created_at - timedelta(seconds=1)
        )


def test_environment_rejects_deletion_before_creation() -> None:
    created_at = datetime(2026, 1, 2, tzinfo=UTC)

    with pytest.raises(InvalidEnvironment):
        make_environment(
            created_at=created_at,
            updated_at=created_at,
            deleted_at=created_at - timedelta(seconds=1),
        )


def test_environment_rejects_naive_timestamps() -> None:
    created_at = datetime(2026, 1, 1)

    with pytest.raises(InvalidEnvironment):
        make_environment(created_at=created_at, updated_at=created_at)
