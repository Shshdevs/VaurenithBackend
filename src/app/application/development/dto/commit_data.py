from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CommitData:
    id: UUID
    repository_id: UUID
    hash: str
    author_name: str | None
    author_email: str | None
    message: str | None
    committed_at: datetime | None
    changed_files: Any | None
    cached_at: datetime | None

    @classmethod
    def from_commit(cls, commit) -> "CommitData":
        return cls(
            id=commit.id,
            repository_id=commit.repository_id,
            hash=commit.hash,
            author_name=commit.author_name,
            author_email=commit.author_email,
            message=commit.message,
            committed_at=commit.committed_at,
            changed_files=commit.changed_files,
            cached_at=commit.cached_at,
        )
