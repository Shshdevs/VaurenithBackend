from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.application.common.exceptions import InvalidInput
from app.application.projects.exceptions import EnvironmentNotFound
from app.application.projects.use_cases.environments import (
    CreateEnvironment,
    DeleteEnvironment,
    GetEnvironment,
    GetProjectEnvironments,
    UpdateEnvironment,
)
from app.domain.projects import Environment, EnvironmentName, EnvironmentType


class FakeEnvironmentRepository:
    def __init__(self, environments: list[Environment] | None = None) -> None:
        self.environments = {item.id: item for item in environments or []}
        self.created: Environment | None = None
        self.updated: Environment | None = None

    async def get_by_id(self, environment_id: UUID) -> Environment | None:
        return self.environments.get(environment_id)

    async def get_active_by_project_id(self, project_id: UUID) -> list[Environment]:
        return [
            item
            for item in self.environments.values()
            if item.project_id == project_id and item.deleted_at is None
        ]

    async def create(self, environment: Environment) -> None:
        self.created = environment
        self.environments[environment.id] = environment

    async def update(self, environment: Environment) -> bool:
        if environment.id not in self.environments:
            return False
        self.updated = environment
        self.environments[environment.id] = environment
        return True

    async def delete(self, environment_id: UUID) -> bool:
        return self.environments.pop(environment_id, None) is not None


def make_environment(
    project_id: UUID | None = None,
    name: str = "Production",
    environment_id: UUID | None = None,
) -> Environment:
    now = datetime.now(UTC)
    return Environment(
        entity_id=environment_id or uuid4(),
        project_id=project_id or uuid4(),
        name=EnvironmentName(name),
        environment_type=EnvironmentType.PRODUCTION,
        description="Production environment",
        configuration={"region": "eu"},
        version=1,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
async def test_create_environment_persists_entity_and_returns_data() -> None:
    project_id = uuid4()
    repository = FakeEnvironmentRepository()
    use_case = CreateEnvironment(repository)

    result = await use_case.execute(
        project_id=project_id,
        name="  Production  ",
        environment_type=EnvironmentType.PRODUCTION,
        description="Production environment",
        configuration={"region": "eu"},
    )

    assert repository.created is not None
    assert repository.created.project_id == project_id
    assert repository.created.name == "Production"
    assert result.project_id == project_id
    assert result.name == "Production"
    assert result.slug == "production"
    assert result.environment_type == EnvironmentType.PRODUCTION
    assert result.configuration == {"region": "eu"}


@pytest.mark.anyio
async def test_create_environment_rejects_invalid_name() -> None:
    repository = FakeEnvironmentRepository()
    use_case = CreateEnvironment(repository)

    with pytest.raises(InvalidInput):
        await use_case.execute(
            project_id=uuid4(),
            name="  ",
            environment_type=EnvironmentType.PRODUCTION,
        )

    assert repository.created is None


@pytest.mark.anyio
async def test_get_environment_returns_data_or_raises_not_found() -> None:
    environment = make_environment()
    use_case = GetEnvironment(FakeEnvironmentRepository([environment]))

    result = await use_case.execute(environment.id)

    assert result.id == environment.id
    assert result.slug == environment.slug
    with pytest.raises(EnvironmentNotFound):
        await use_case.execute(uuid4())


@pytest.mark.anyio
async def test_get_project_environments_returns_only_project_environments() -> None:
    project_id = uuid4()
    first = make_environment(project_id=project_id, name="Development")
    second = make_environment(project_id=project_id, name="Production")
    other_project_environment = make_environment()
    use_case = GetProjectEnvironments(
        FakeEnvironmentRepository([first, second, other_project_environment])
    )

    result = await use_case.execute(project_id)

    assert [item.id for item in result] == [first.id, second.id]


@pytest.mark.anyio
async def test_update_environment_persists_changes_and_preserves_creation_time() -> None:
    environment = make_environment()
    repository = FakeEnvironmentRepository([environment])
    use_case = UpdateEnvironment(repository)

    result = await use_case.execute(
        environment_id=environment.id,
        project_id=environment.project_id,
        name="Staging",
        environment_type=EnvironmentType.STAGING,
        description="Staging environment",
        configuration={"region": "us"},
        version=2,
    )

    assert repository.updated is not None
    assert repository.updated.created_at == environment.created_at
    assert repository.updated.updated_at > environment.updated_at
    assert result.name == "Staging"
    assert result.slug == "staging"
    assert result.environment_type == EnvironmentType.STAGING
    assert result.version == 2
    assert result.configuration == {"region": "us"}


@pytest.mark.anyio
async def test_update_environment_rejects_missing_environment_or_invalid_name() -> None:
    repository = FakeEnvironmentRepository()
    use_case = UpdateEnvironment(repository)
    environment_id = uuid4()

    with pytest.raises(EnvironmentNotFound):
        await use_case.execute(
            environment_id=environment_id,
            project_id=uuid4(),
            name="Staging",
            environment_type=EnvironmentType.STAGING,
        )

    environment = make_environment()
    repository.environments[environment.id] = environment
    with pytest.raises(InvalidInput):
        await use_case.execute(
            environment_id=environment.id,
            project_id=environment.project_id,
            name="  ",
            environment_type=EnvironmentType.STAGING,
        )


@pytest.mark.anyio
async def test_delete_environment_deletes_existing_and_reports_missing() -> None:
    environment = make_environment()
    repository = FakeEnvironmentRepository([environment])
    use_case = DeleteEnvironment(repository)

    await use_case.execute(environment.id)

    assert environment.id not in repository.environments
    with pytest.raises(EnvironmentNotFound):
        await use_case.execute(environment.id)
