from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.domain.development.entities.branch import Branch


class BranchRepositoryStub:
    def __init__(self, user_id: UUID, repository_ids: set[UUID]) -> None:
        self.user_id = user_id
        self.repository_ids = repository_ids
        self.branches: dict[UUID, Branch] = {}

    async def get_by_id(self, user_id: UUID, branch_id: UUID):
        branch = self.branches.get(branch_id)
        if user_id != self.user_id or branch is None:
            return None
        if branch.repository_id not in self.repository_ids:
            return None
        return branch

    async def get_by_repository(self, user_id: UUID, repository_id: UUID):
        if user_id != self.user_id or repository_id not in self.repository_ids:
            return []
        return sorted(
            (
                branch
                for branch in self.branches.values()
                if branch.repository_id == repository_id
            ),
            key=lambda branch: (branch.is_remote, branch.name, branch.id),
        )

    async def get_by_name(
        self, user_id: UUID, repository_id: UUID, name: str, is_remote: bool
    ):
        for branch in self.branches.values():
            if (
                user_id == self.user_id
                and repository_id in self.repository_ids
                and branch.repository_id == repository_id
                and branch.name == name
                and branch.is_remote == is_remote
            ):
                return branch
        return None

    async def create(self, user_id: UUID, branch: Branch) -> None:
        if user_id != self.user_id or branch.repository_id not in self.repository_ids:
            raise ValueError("Repository not found")
        if branch.is_current:
            for existing in self.branches.values():
                if existing.repository_id == branch.repository_id and existing.is_current:
                    self.branches[existing.id] = Branch(
                        entity_id=existing.id,
                        repository_id=existing.repository_id,
                        name=existing.name,
                        commit_hash=existing.commit_hash,
                        is_remote=existing.is_remote,
                        is_current=False,
                        last_updated_at=existing.last_updated_at,
                        last_synced_at=existing.last_synced_at,
                    )
        self.branches[branch.id] = branch

    async def update(self, user_id: UUID, branch: Branch) -> bool:
        existing = await self.get_by_id(user_id, branch.id)
        if existing is None:
            return False
        if branch.is_current:
            for current in self.branches.values():
                if (
                    current.repository_id == branch.repository_id
                    and current.id != branch.id
                    and current.is_current
                ):
                    self.branches[current.id] = Branch(
                        entity_id=current.id,
                        repository_id=current.repository_id,
                        name=current.name,
                        commit_hash=current.commit_hash,
                        is_remote=current.is_remote,
                        is_current=False,
                        last_updated_at=current.last_updated_at,
                        last_synced_at=current.last_synced_at,
                    )
        self.branches[branch.id] = branch
        return True

    async def delete(self, user_id: UUID, branch_id: UUID) -> bool:
        branch = await self.get_by_id(user_id, branch_id)
        if branch is None:
            return False
        del self.branches[branch_id]
        return True


class RepositoryRepositoryStub:
    def __init__(self, repository_ids: set[UUID]) -> None:
        self.repository_ids = repository_ids

    async def get_by_id(self, user_id: UUID, repository_id: UUID):
        return (
            SimpleNamespace(id=repository_id)
            if repository_id in self.repository_ids
            else None
        )


def make_branch(repository_id: UUID, **overrides) -> Branch:
    now = datetime.now(UTC)
    values = {
        "entity_id": uuid4(),
        "repository_id": repository_id,
        "name": "main",
        "commit_hash": "a" * 40,
        "is_remote": False,
        "is_current": False,
        "last_updated_at": now,
        "last_synced_at": now,
    }
    values.update(overrides)
    return Branch(**values)
