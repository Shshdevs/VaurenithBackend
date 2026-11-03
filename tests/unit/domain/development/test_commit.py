from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.domain.development.entities.commit import Commit
from app.domain.development.exceptions import InvalidCommit, InvalidCommitHash


def make_commit(**overrides: Any) -> Commit:
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "repository_id": uuid4(),
        "hash": "a" * 40,
        "committed_at": datetime(2026, 1, 1, tzinfo=UTC),
        "cached_at": datetime(2026, 1, 2, tzinfo=UTC),
    }
    values.update(overrides)
    return Commit(**values)


def test_commit_normalizes_hash_and_author_values() -> None:
    commit = make_commit(
        hash="A" * 40,
        author_name="  Developer  ",
        author_email="  not-an-email  ",
    )

    assert commit.hash == "a" * 40
    assert commit.author_name == "Developer"
    assert commit.author_email == "not-an-email"


@pytest.mark.parametrize("commit_hash", ["", "bad-hash", "a" * 39, "a" * 65])
def test_commit_rejects_invalid_hash(commit_hash: str) -> None:
    with pytest.raises(InvalidCommitHash):
        make_commit(hash=commit_hash)


def test_commit_rejects_oversized_author_fields() -> None:
    with pytest.raises(InvalidCommit):
        make_commit(author_name="x" * 256)
    with pytest.raises(InvalidCommit):
        make_commit(author_email="x" * 321)


def test_commit_rejects_naive_timestamps() -> None:
    with pytest.raises(InvalidCommit):
        make_commit(committed_at=datetime(2026, 1, 1))


def test_commit_changed_files_are_defensively_copied() -> None:
    changed_files = [{"path": "src/app.py", "status": "modified"}]
    expected = deepcopy(changed_files)
    commit = make_commit(changed_files=changed_files)
    changed_files[0]["path"] = "changed.py"

    assert commit.changed_files == expected
    returned_files = commit.changed_files
    assert returned_files is not None
    returned_files[0]["path"] = "returned.py"

    assert commit.changed_files == expected
