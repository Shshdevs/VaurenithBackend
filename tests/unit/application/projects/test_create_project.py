from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.projects import CreateProject
from app.domain.identity import EmailAddress, TokenHash
from app.domain.projects import Project, ProjectType


class FakeProjectRepository:
    def __init__(self) -> None:
        self.created: Project | None = None

    async def create(self, project: Project) -> None:
        self.created = project


def make_identity() -> VerifiedIdentity:
    now = datetime.now(UTC)
    return VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("project-owner@example.test"),
        auth_provider="test-provider",
        expires_at=now + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


@pytest.mark.anyio
async def test_create_project_uses_defaults_and_persists_project() -> None:
    identity = make_identity()
    repository = FakeProjectRepository()
    use_case = CreateProject(repository)

    result = await use_case.execute(
        identity=identity,
        name="  Project alpha  ",
        project_type=ProjectType.SOFTWARE,
    )

    assert repository.created is not None
    assert result.id == repository.created.id
    assert result.user_id == identity.user_id
    assert result.name == "Project alpha"
    assert result.slug == "project-alpha"
    assert result.project_type == ProjectType.SOFTWARE.value
    assert result.status == "active"
    assert result.version == 1
    assert result.description is None
    assert result.metadata is None
    assert result.created_at == repository.created.created_at
    assert result.updated_at == repository.created.updated_at
    assert result.deleted_at is None


@pytest.mark.anyio
async def test_create_project_preserves_custom_version_and_data() -> None:
    repository = FakeProjectRepository()
    use_case = CreateProject(repository)
    metadata: dict[str, Any] = {"environment": "production"}

    result = await use_case.execute(
        identity=make_identity(),
        name="Project beta",
        project_type=ProjectType.FULLSTACK,
        version=4,
        description="A full stack project",
        metadata=metadata,
    )

    assert repository.created is not None
    assert repository.created.version == 4
    assert result.version == 4
    assert result.description == "A full stack project"
    assert result.metadata == metadata
    assert result.project_type == ProjectType.FULLSTACK.value


@pytest.mark.anyio
async def test_create_project_rejects_invalid_name_without_saving() -> None:
    repository = FakeProjectRepository()
    use_case = CreateProject(repository)

    with pytest.raises(InvalidInput, match="Project name is invalid"):
        await use_case.execute(
            identity=make_identity(),
            name="   ",
            project_type=ProjectType.SOFTWARE,
        )

    assert repository.created is None
