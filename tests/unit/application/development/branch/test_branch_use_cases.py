from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from tests.support import NoOpUnitOfWork
from tests.unit.application.development.branch.conftest import (
    BranchRepositoryStub,
    RepositoryRepositoryStub,
    make_branch,
)

from app.application.common.exceptions import Conflict, InvalidInput
from app.application.development import (
    BranchNotFound,
    CreateBranch,
    DeleteBranch,
    GetBranch,
    GetRepositoryBranches,
    RepositoryNotFound,
    UpdateBranch,
)
from app.application.identity import VerifiedIdentity
from app.domain.identity import EmailAddress, TokenHash


def make_identity() -> VerifiedIdentity:
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="branch-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_use_cases(identity: VerifiedIdentity, repository_id):
    branch_repository = BranchRepositoryStub(identity.user_id, {repository_id})
    repository_repository = RepositoryRepositoryStub({repository_id})
    unit_of_work = NoOpUnitOfWork()
    return (
        branch_repository,
        CreateBranch(branch_repository, repository_repository, unit_of_work),
        GetBranch(branch_repository),
        GetRepositoryBranches(branch_repository, repository_repository),
        UpdateBranch(branch_repository, unit_of_work),
        DeleteBranch(branch_repository, unit_of_work),
    )


@pytest.mark.anyio
async def test_branch_lifecycle_and_current_branch_switch() -> None:
    identity = make_identity()
    repository_id = uuid4()
    branches, create, get, list_branches, update, delete = make_use_cases(
        identity, repository_id
    )
    first = await create.create_branch(
        identity, repository_id, "main", "a" * 40, is_current=True
    )
    second = await create.create_branch(
        identity, repository_id, "feature/search", "b" * 40, is_remote=True
    )

    assert (await get.get_branch(identity, first.id)).is_current
    listed = await list_branches.get_repository_branches(identity, repository_id)
    assert [item.name for item in listed] == ["main", "feature/search"]

    updated = await update.update_branch(
        identity,
        second.id,
        name="feature/index",
        commit_hash="c" * 40,
        is_remote=False,
        is_current=True,
        last_updated_at=datetime.now(UTC),
        last_synced_at=datetime.now(UTC),
    )

    assert updated.name == "feature/index"
    assert updated.commit_hash == "c" * 40
    assert updated.is_current
    assert not (await get.get_branch(identity, first.id)).is_current

    await delete.delete_branch(identity, second.id)
    with pytest.raises(BranchNotFound):
        await get.get_branch(identity, second.id)
    assert set(branches.branches) == {first.id}


@pytest.mark.anyio
async def test_branch_creation_validates_repository_name_and_uniqueness_scope() -> None:
    identity = make_identity()
    repository_id = uuid4()
    _, create, _, list_branches, _, _ = make_use_cases(identity, repository_id)

    with pytest.raises(RepositoryNotFound):
        await create.create_branch(identity, uuid4(), "main")
    with pytest.raises(InvalidInput):
        await create.create_branch(identity, repository_id, "bad name")
    with pytest.raises(InvalidInput):
        await create.create_branch(identity, repository_id, "main", "z" * 40)

    await create.create_branch(identity, repository_id, "main")
    with pytest.raises(Conflict):
        await create.create_branch(identity, repository_id, "main")
    remote = await create.create_branch(identity, repository_id, "main", is_remote=True)
    assert remote.is_remote
    assert len(await list_branches.get_repository_branches(identity, repository_id)) == 2


@pytest.mark.anyio
async def test_branch_reads_and_updates_are_scoped_to_owner() -> None:
    identity = make_identity()
    repository_id = uuid4()
    branches, _, get, list_branches, update, delete = make_use_cases(
        identity, repository_id
    )
    branch = make_branch(repository_id)
    branches.branches[branch.id] = branch
    other_identity = make_identity()

    with pytest.raises(BranchNotFound):
        await get.get_branch(other_identity, branch.id)
    with pytest.raises(RepositoryNotFound):
        await list_branches.get_repository_branches(identity, uuid4())
    with pytest.raises(BranchNotFound):
        await update.update_branch(
            other_identity,
            branch.id,
            name=branch.name,
            commit_hash=branch.commit_hash,
            is_remote=branch.is_remote,
            is_current=branch.is_current,
            last_updated_at=branch.last_updated_at,
            last_synced_at=branch.last_synced_at,
        )
    with pytest.raises(BranchNotFound):
        await delete.delete_branch(other_identity, branch.id)
