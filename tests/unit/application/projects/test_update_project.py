from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpRecordChange, NoOpUnitOfWork

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectNotFound, ProjectVersionConflict
from app.application.projects.use_cases.projects.update_project import UpdateProject
from app.domain.identity import EmailAddress, TokenHash
from app.domain.projects import Project, ProjectName, ProjectStatus, ProjectType


class FakeProjectRepository:
    def __init__(
        self,
        project: Project | None,
        update_result: bool = True,
    ) -> None:
        self.project = project
        self.update_result = update_result
        self.requested_owner_id: UUID | None = None
        self.updated_project: Project | None = None
        self.expected_version: int | None = None

    async def get_by_id(self, user_id: UUID, project_id: UUID) -> Project | None:
        self.requested_owner_id = user_id
        if (
            self.project is None
            or self.project.id != project_id
            or self.project.user_id != user_id
        ):
            return None
        return self.project

    async def update(self, user_id: UUID, project: Project, expected_version: int) -> bool:
        self.updated_project = project
        self.expected_version = expected_version
        return self.update_result


def make_identity(user_id: UUID | None = None) -> VerifiedIdentity:
    now = datetime.now(UTC)
    return VerifiedIdentity(
        user_id=user_id or uuid4(),
        email=EmailAddress("project-owner@example.test"),
        auth_provider="test-provider",
        expires_at=now + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_project(user_id: UUID, version: int = 1) -> Project:
    created_at = datetime(2025, 1, 1, tzinfo=UTC)
    return Project(
        entity_id=uuid4(),
        user_id=user_id,
        name=ProjectName("Original project"),
        description="Original description",
        project_type=ProjectType.SOFTWARE,
        status=ProjectStatus.ACTIVE,
        metadata={"environment": "development"},
        version=version,
        created_at=created_at,
        updated_at=created_at,
    )


@pytest.mark.anyio
async def test_update_project_persists_changes_and_returns_project_data() -> None:
    identity = make_identity()
    existing_project = make_project(identity.user_id)
    repository = FakeProjectRepository(existing_project)
    use_case = UpdateProject(repository, NoOpRecordChange(), NoOpUnitOfWork())

    result = await use_case.execute(
        identity=identity,
        project_id=existing_project.id,
        name="  Updated project  ",
        project_type=ProjectType.FULLSTACK,
        status=ProjectStatus.ARCHIVED,
        expected_version=1,
        description="Updated description",
        metadata={"environment": "production"},
    )

    assert repository.requested_owner_id == identity.user_id
    assert repository.updated_project is not None
    assert repository.updated_project.id == existing_project.id
    assert repository.updated_project.user_id == identity.user_id
    assert repository.updated_project.name == "Updated project"
    assert repository.updated_project.project_type is ProjectType.FULLSTACK
    assert repository.updated_project.status is ProjectStatus.ARCHIVED
    assert repository.updated_project.version == 2
    assert repository.expected_version == 1
    assert repository.updated_project.description == "Updated description"
    assert repository.updated_project.metadata == {"environment": "production"}
    assert repository.updated_project.created_at == existing_project.created_at
    assert repository.updated_project.updated_at > existing_project.updated_at
    assert result.id == existing_project.id
    assert result.slug == "updated-project"
    assert result.status == ProjectStatus.ARCHIVED.value
    assert result.updated_at == repository.updated_project.updated_at


@pytest.mark.anyio
async def test_update_project_rejects_project_owned_by_another_user() -> None:
    identity = make_identity()
    existing_project = make_project(uuid4())
    repository = FakeProjectRepository(existing_project)
    use_case = UpdateProject(repository, NoOpRecordChange(), NoOpUnitOfWork())

    with pytest.raises(ProjectNotFound):
        await use_case.execute(
            identity=identity,
            project_id=existing_project.id,
            name="Updated project",
            project_type=ProjectType.SOFTWARE,
            status=ProjectStatus.ACTIVE,
            expected_version=1,
            description=None,
            metadata=None,
        )

    assert repository.requested_owner_id == identity.user_id
    assert repository.updated_project is None


@pytest.mark.anyio
async def test_update_project_reports_conflict_if_repository_rejects_update() -> None:
    identity = make_identity()
    existing_project = make_project(identity.user_id)
    repository = FakeProjectRepository(existing_project, update_result=False)
    use_case = UpdateProject(repository, NoOpRecordChange(), NoOpUnitOfWork())

    with pytest.raises(ProjectVersionConflict):
        await use_case.execute(
            identity=identity,
            project_id=existing_project.id,
            name="Updated project",
            project_type=ProjectType.SOFTWARE,
            status=ProjectStatus.ACTIVE,
            expected_version=1,
            description=None,
            metadata=None,
        )

    assert repository.updated_project is not None


@pytest.mark.anyio
async def test_update_project_rejects_invalid_name_without_persisting() -> None:
    identity = make_identity()
    existing_project = make_project(identity.user_id)
    repository = FakeProjectRepository(existing_project)
    use_case = UpdateProject(repository, NoOpRecordChange(), NoOpUnitOfWork())

    with pytest.raises(InvalidInput):
        await use_case.execute(
            identity=identity,
            project_id=existing_project.id,
            name="   ",
            project_type=ProjectType.SOFTWARE,
            status=ProjectStatus.ACTIVE,
            expected_version=1,
            description=None,
            metadata=None,
        )

    assert repository.updated_project is None


@pytest.mark.anyio
async def test_update_project_rejects_stale_expected_version_before_writing() -> None:
    identity = make_identity()
    existing_project = make_project(identity.user_id, version=4)
    repository = FakeProjectRepository(existing_project)

    with pytest.raises(ProjectVersionConflict, match="current version is 4"):
        await UpdateProject(repository, NoOpRecordChange(), NoOpUnitOfWork()).execute(
            identity=identity,
            project_id=existing_project.id,
            name="Updated project",
            project_type=ProjectType.SOFTWARE,
            status=ProjectStatus.ACTIVE,
            expected_version=3,
            description=None,
            metadata=None,
        )

    assert repository.updated_project is None
