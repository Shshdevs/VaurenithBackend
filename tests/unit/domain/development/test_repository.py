from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.domain.development.entities.repository import Repository
from app.domain.development.enums import RepositoryType
from app.domain.development.exceptions import InvalidRepository


def make_repository(**overrides: Any) -> Repository:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "project_id": uuid4(),
        "name": "  Backend  ",
        "created_at": created_at,
        "updated_at": created_at,
    }
    values.update(overrides)
    return Repository(**values)


def test_repository_normalizes_name_and_optional_values() -> None:
    repository = make_repository(
        remote_url=" git@github.com:owner/repo.git ",
        default_branch="main",
    )

    assert repository.name == "Backend"
    assert repository.repository_type is RepositoryType.GIT
    assert repository.remote_url == "git@github.com:owner/repo.git"
    assert repository.default_branch == "main"
    assert repository.version == 1


def test_repository_normalizes_blank_optional_values_to_none() -> None:
    repository = make_repository(remote_url="  ", default_branch="  ")

    assert repository.remote_url is None
    assert repository.default_branch is None


@pytest.mark.parametrize("name", ["", "   ", "x" * 256])
def test_repository_rejects_invalid_name(name: str) -> None:
    with pytest.raises(InvalidRepository):
        make_repository(name=name)


@pytest.mark.parametrize("default_branch", ["bad branch", "topic..name", "x" * 256])
def test_repository_rejects_invalid_default_branch(default_branch: str) -> None:
    with pytest.raises(InvalidRepository):
        make_repository(default_branch=default_branch)


def test_repository_rejects_update_before_creation() -> None:
    created_at = datetime(2026, 1, 2, tzinfo=UTC)

    with pytest.raises(InvalidRepository):
        make_repository(
            created_at=created_at,
            updated_at=created_at - timedelta(seconds=1),
        )


def test_repository_rejects_naive_timestamps() -> None:
    created_at = datetime(2026, 1, 1)

    with pytest.raises(InvalidRepository):
        make_repository(created_at=created_at, updated_at=created_at)
