from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class BranchData:
    id: UUID
    repository_id: UUID
    name: str
    commit_hash: str | None
    is_remote: bool
    is_current: bool
    last_updated_at: datetime | None
    last_synced_at: datetime | None

    @classmethod
    def from_branch(cls, branch) -> "BranchData":
        return cls(
            id=branch.id,
            repository_id=branch.repository_id,
            name=branch.name,
            commit_hash=branch.commit_hash,
            is_remote=branch.is_remote,
            is_current=branch.is_current,
            last_updated_at=branch.last_updated_at,
            last_synced_at=branch.last_synced_at,
        )
