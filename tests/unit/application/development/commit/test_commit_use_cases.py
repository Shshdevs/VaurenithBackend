from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from tests.support import NoOpUnitOfWork
from tests.unit.application.development.commit.conftest import (
    CommitRepositoryStub,
    RepositoryRepositoryStub,
    make_commit,
)

from app.application.common.exceptions import Conflict, InvalidInput
from app.application.development import (
    CommitNotFound,
    CreateCommit,
    GetCommit,
    GetRepositoryCommits,
    RepositoryNotFound,
)
from app.application.identity import VerifiedIdentity
from app.domain.identity import EmailAddress, TokenHash


def make_identity() -> VerifiedIdentity:
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="commit-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_use_cases(identity: VerifiedIdentity, repository_id):
    commit_repository = CommitRepositoryStub(identity.user_id, {repository_id})
    repository_repository = RepositoryRepositoryStub({repository_id})
    return (
        commit_repository,
        CreateCommit(commit_repository, repository_repository, NoOpUnitOfWork()),
        GetCommit(commit_repository),
        GetRepositoryCommits(commit_repository, repository_repository),
    )


@pytest.mark.anyio
async def test_commit_can_be_cached_and_read_by_id_and_repository() -> None:
    identity = make_identity()
    repository_id = uuid4()
    repository, create, get, list_commits = make_use_cases(identity, repository_id)
    committed_at = datetime.now(UTC)

    created = await create.create_commit(
        identity,
        repository_id,
        "A" * 40,
        author_name=" Ada Lovelace ",
        author_email="ada@example.test",
        message="Initial commit",
        committed_at=committed_at,
        changed_files=["src/main.py"],
    )

    assert created.hash == "a" * 40
    assert created.author_name == "Ada Lovelace"
    assert created.committed_at == committed_at
    assert created.cached_at is not None
    assert await get.get_commit(identity, created.id) == created
    assert await list_commits.get_repository_commits(identity, repository_id) == [created]
    assert len(repository.commits) == 1


@pytest.mark.anyio
async def test_commit_creation_validates_repository_hash_and_duplicates() -> None:
    identity = make_identity()
    repository_id = uuid4()
    _, create, _, _ = make_use_cases(identity, repository_id)

    with pytest.raises(RepositoryNotFound):
        await create.create_commit(identity, uuid4(), "a" * 40)
    with pytest.raises(InvalidInput):
        await create.create_commit(identity, repository_id, "not-a-git-hash")

    await create.create_commit(identity, repository_id, "B" * 40)
    with pytest.raises(Conflict):
        await create.create_commit(identity, repository_id, "b" * 40)


@pytest.mark.anyio
async def test_commit_reads_are_scoped_to_identity_and_repository() -> None:
    identity = make_identity()
    repository_id = uuid4()
    repository, _, get, list_commits = make_use_cases(identity, repository_id)
    commit = make_commit(repository_id)
    repository.commits[commit.id] = commit
    other_identity = make_identity()
    _, _, other_get, _ = make_use_cases(other_identity, uuid4())

    with pytest.raises(CommitNotFound):
        await other_get.get_commit(other_identity, commit.id)
    with pytest.raises(RepositoryNotFound):
        await list_commits.get_repository_commits(identity, uuid4())
