from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpUnitOfWork

from app.application.development import (
    CreateRepository,
    DeleteRepository,
    GetProjectRepositories,
    GetRepository,
    RepositoryNotFound,
    RepositoryVersionConflict,
    UpdateRepository,
)
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectNotFound
from app.domain.development.entities.repository import Repository
from app.domain.development.enums import RepositoryType
from app.domain.identity import EmailAddress, TokenHash
from app.domain.synchronization import ChangeOperation


class RepositoryRepositoryStub:
    def __init__(self) -> None:
        self.repositories: dict[UUID, Repository] = {}

    async def get_by_id(self, user_id: UUID, repository_id: UUID) -> Repository | None:
        value = self.repositories.get(repository_id)
        if value is None or value.deleted_at is not None:
            return None
        return value if value.project_id in self.owned_projects[user_id] else None

    async def get_by_user(self, user_id: UUID) -> list[Repository]:
        return [
            value
            for value in self.repositories.values()
            if value.project_id in self.owned_projects.get(user_id, set())
            and value.deleted_at is None
        ]

    async def get_by_project(self, user_id: UUID, project_id: UUID) -> list[Repository]:
        return [
            value
            for value in await self.get_by_user(user_id)
            if value.project_id == project_id
        ]

    async def create(self, repository: Repository) -> None:
        self.repositories[repository.id] = repository

    async def update(
        self, user_id: UUID, repository: Repository, expected_version: int
    ) -> bool:
        existing = await self.get_by_id(user_id, repository.id)
        if existing is None or existing.version != expected_version:
            return False
        self.repositories[repository.id] = repository
        return True

    async def delete(
        self, user_id: UUID, repository_id: UUID, expected_version: int
    ) -> bool:
        existing = await self.get_by_id(user_id, repository_id)
        if existing is None or existing.version != expected_version:
            return False
        now = datetime.now(UTC)
        self.repositories[repository_id] = Repository(
            entity_id=existing.id,
            project_id=existing.project_id,
            name=existing.name,
            description=existing.description,
            remote_url=existing.remote_url,
            default_branch=existing.default_branch,
            repository_type=existing.repository_type,
            version=expected_version + 1,
            created_at=existing.created_at,
            updated_at=now,
            deleted_at=now,
        )
        return True

    owned_projects: dict[UUID, set[UUID]] = {}


class ProjectRepositoryStub:
    def __init__(self, project_ids: set[UUID]) -> None:
        self.project_ids = project_ids

    async def get_by_id(self, user_id: UUID, project_id: UUID):
        return SimpleNamespace(id=project_id) if project_id in self.project_ids else None


class RecordChangeStub:
    def __init__(self) -> None:
        self.records: list[tuple] = []

    async def execute(self, *args) -> None:
        self.records.append(args)


def make_identity() -> VerifiedIdentity:
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="repository-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_repositories(identity: VerifiedIdentity, project_id: UUID):
    repository = RepositoryRepositoryStub()
    repository.owned_projects = {identity.user_id: {project_id}}
    projects = ProjectRepositoryStub({project_id})
    recorder = RecordChangeStub()
    create = CreateRepository(repository, projects, recorder, NoOpUnitOfWork())
    get = GetRepository(repository)
    list_project = GetProjectRepositories(repository, projects)
    update = UpdateRepository(repository, recorder, NoOpUnitOfWork())
    delete = DeleteRepository(repository, recorder, NoOpUnitOfWork())
    return repository, recorder, create, get, list_project, update, delete


@pytest.mark.anyio
async def test_repository_create_update_and_project_scoped_listing() -> None:
    identity = make_identity()
    project_id = uuid4()
    repository, recorder, create, get, list_project, update, _ = make_repositories(
        identity, project_id
    )

    created = await create.create_repository(
        identity,
        project_id,
        "  backend  ",
        "Main service",
        "https://example.test/org/backend.git",
        "main",
        RepositoryType.GIT,
    )
    updated = await update.update_repository(
        identity,
        created.id,
        1,
        "backend-api",
        "Production service",
        "https://example.test/org/backend.git",
        "trunk",
        RepositoryType.GIT,
    )
    listed = await list_project.get_project_repositories(identity, project_id)
    fetched = await get.get_repository(identity, created.id)

    assert created.name == "backend"
    assert updated.version == 2
    assert updated.default_branch == "trunk"
    assert listed == [updated]
    assert fetched == updated
    assert [record[3] for record in recorder.records] == [
        ChangeOperation.INSERT,
        ChangeOperation.UPDATE,
    ]
    assert all("remote_url" not in record[5] for record in recorder.records)


@pytest.mark.anyio
async def test_repository_delete_soft_deletes_and_records_next_version() -> None:
    identity = make_identity()
    project_id = uuid4()
    repository, recorder, create, get, _, _, delete = make_repositories(
        identity, project_id
    )
    created = await create.create_repository(
        identity,
        project_id,
        "backend",
        None,
        None,
        None,
        RepositoryType.GIT,
    )

    await delete.delete_repository(identity, created.id, 1)

    assert repository.repositories[created.id].deleted_at is not None
    assert recorder.records[-1][3] is ChangeOperation.DELETE
    assert recorder.records[-1][4] == 2
    with pytest.raises(RepositoryNotFound):
        await get.get_repository(identity, created.id)


@pytest.mark.anyio
async def test_repository_create_checks_project_ownership_and_versions() -> None:
    identity = make_identity()
    project_id = uuid4()
    owned_project_id = uuid4()
    _, _, create, _, _, update, _ = make_repositories(identity, owned_project_id)

    with pytest.raises(ProjectNotFound):
        await create.create_repository(
            identity,
            project_id,
            "backend",
            None,
            None,
            None,
            RepositoryType.GIT,
        )
    created = await create.create_repository(
        identity,
        owned_project_id,
        "backend",
        None,
        None,
        None,
        RepositoryType.GIT,
    )
    with pytest.raises(RepositoryVersionConflict):
        await update.update_repository(
            identity,
            created.id,
            2,
            "backend",
            None,
            None,
            None,
            RepositoryType.GIT,
        )
