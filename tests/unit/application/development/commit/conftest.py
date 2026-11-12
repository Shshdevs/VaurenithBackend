from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.domain.development.entities.commit import Commit


class CommitRepositoryStub:
    def __init__(self, user_id: UUID, repository_ids: set[UUID]) -> None:
        self.user_id = user_id
        self.repository_ids = repository_ids
        self.commits: dict[UUID, Commit] = {}

    async def get_by_id(self, user_id: UUID, commit_id: UUID):
        commit = self.commits.get(commit_id)
        if user_id != self.user_id or commit is None:
            return None
        if commit.repository_id not in self.repository_ids:
            return None
        return commit

    async def get_by_repository(self, user_id: UUID, repository_id: UUID):
        if user_id != self.user_id or repository_id not in self.repository_ids:
            return []
        return [
            commit
            for commit in self.commits.values()
            if commit.repository_id == repository_id
        ]

    async def get_by_hash(self, user_id: UUID, repository_id: UUID, commit_hash: str):
        for commit in self.commits.values():
            if (
                user_id == self.user_id
                and repository_id in self.repository_ids
                and commit.repository_id == repository_id
                and commit.hash == commit_hash
            ):
                return commit
        return None

    async def create(self, user_id: UUID, commit: Commit) -> None:
        if user_id != self.user_id or commit.repository_id not in self.repository_ids:
            raise ValueError("Repository not found")
        self.commits[commit.id] = commit


class RepositoryRepositoryStub:
    def __init__(self, repository_ids: set[UUID]) -> None:
        self.repository_ids = repository_ids

    async def get_by_id(self, user_id: UUID, repository_id: UUID):
        return (
            SimpleNamespace(id=repository_id)
            if repository_id in self.repository_ids
            else None
        )


def make_commit(repository_id: UUID, **overrides) -> Commit:
    values = {
        "entity_id": uuid4(),
        "repository_id": repository_id,
        "hash": "a" * 40,
        "author_name": "Ada Lovelace",
        "author_email": "ada@example.test",
        "message": "Initial commit",
        "committed_at": datetime.now(UTC),
        "changed_files": ["src/main.py"],
        "cached_at": datetime.now(UTC),
    }
    values.update(overrides)
    return Commit(**values)
