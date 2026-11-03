from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.domain.development.entities.branch import Branch
from app.domain.development.exceptions import InvalidBranch, InvalidCommitHash


def make_branch(**overrides: Any) -> Branch:
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "repository_id": uuid4(),
        "name": "feature/search",
        "commit_hash": "a" * 40,
        "last_updated_at": datetime(2026, 1, 1, tzinfo=UTC),
        "last_synced_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return Branch(**values)


def test_branch_exposes_normalized_values() -> None:
    branch = make_branch(commit_hash="A" * 40)

    assert branch.name == "feature/search"
    assert branch.commit_hash == "a" * 40
    assert branch.is_remote is False
    assert branch.is_current is False
    assert branch.last_updated_at == datetime(2026, 1, 1, tzinfo=UTC)


@pytest.mark.parametrize(
    "name",
    [
        "",
        "feature name",
        "feature..name",
        "feature//name",
        ".hidden",
        "feature/.hidden",
        "feature.lock",
        "feature.",
        "@",
        "-feature",
        "feature\\name",
        "feature@{1}",
        "x" * 256,
    ],
)
def test_branch_rejects_invalid_git_branch_names(name: str) -> None:
    with pytest.raises(InvalidBranch):
        make_branch(name=name)


@pytest.mark.parametrize("commit_hash", ["", "xyz", "a" * 39, "a" * 65])
def test_branch_rejects_invalid_commit_hash(commit_hash: str) -> None:
    with pytest.raises(InvalidCommitHash):
        make_branch(commit_hash=commit_hash)


def test_branch_rejects_naive_timestamps() -> None:
    with pytest.raises(InvalidBranch):
        make_branch(last_synced_at=datetime(2026, 1, 1))
