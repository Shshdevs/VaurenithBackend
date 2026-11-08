from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.projects.environment import build_environment_route
from app.application.identity import VerifiedIdentity
from app.application.projects.exceptions import ProjectNotFound
from app.application.projects.use_cases.environments import (
    CreateEnvironment,
    DeleteEnvironment,
    GetEnvironment,
    GetProjectEnvironments,
    UpdateEnvironment,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.projects import Environment, EnvironmentName, EnvironmentType


class FakeEnvironmentRepository:
    def __init__(self) -> None:
        self.environments: dict[UUID, Environment] = {}

    async def get_by_id(self, environment_id: UUID) -> Environment | None:
        return self.environments.get(environment_id)

    async def get_active_by_project_id(self, project_id: UUID) -> list[Environment]:
        return [
            environment
            for environment in self.environments.values()
            if environment.project_id == project_id and environment.deleted_at is None
        ]

    async def create(self, environment: Environment) -> None:
        self.environments[environment.id] = environment

    async def update(self, environment: Environment) -> bool:
        if environment.id not in self.environments:
            return False
        self.environments[environment.id] = environment
        return True

    async def delete(self, environment_id: UUID) -> bool:
        return self.environments.pop(environment_id, None) is not None


class FakeProjectAccess:
    def __init__(self, owned_project_id: UUID) -> None:
        self.owned_project_id = owned_project_id

    async def execute(self, identity: VerifiedIdentity, project_id: UUID) -> None:
        if project_id != self.owned_project_id:
            raise ProjectNotFound(str(project_id))


def make_identity() -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("environment-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def build_test_client(
    project_id: UUID,
) -> tuple[TestClient, FakeEnvironmentRepository]:
    repository = FakeEnvironmentRepository()
    create_environment = CreateEnvironment(repository)
    get_environment = GetEnvironment(repository)
    get_project_environments = GetProjectEnvironments(repository)
    update_environment = UpdateEnvironment(repository)
    delete_environment = DeleteEnvironment(repository)
    project_access = FakeProjectAccess(project_id)
    identity = make_identity()

    def provide_identity() -> VerifiedIdentity:
        return identity

    def provide_project_access() -> FakeProjectAccess:
        return project_access

    def provide_create_environment() -> CreateEnvironment:
        return create_environment

    def provide_get_environment() -> GetEnvironment:
        return get_environment

    def provide_get_project_environments() -> GetProjectEnvironments:
        return get_project_environments

    def provide_update_environment() -> UpdateEnvironment:
        return update_environment

    def provide_delete_environment() -> DeleteEnvironment:
        return delete_environment

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_environment_route(
            create_environment_dependency=provide_create_environment,
            get_environment_dependency=provide_get_environment,
            get_project_environments_dependency=provide_get_project_environments,
            update_environment_dependency=provide_update_environment,
            delete_environment_dependency=provide_delete_environment,
            get_project_dependency=provide_project_access,
            authenticated_identity_dependency=provide_identity,
        )
    )
    return TestClient(app), repository


def test_environment_routes_support_create_list_get_update_and_delete() -> None:
    project_id = uuid4()
    client, repository = build_test_client(project_id)
    collection_url = f"/projects/{project_id}/environments"

    created = client.post(
        collection_url,
        json={
            "name": "  Production  ",
            "environment_type": "production",
            "description": "Production environment",
            "configuration": {"region": "eu"},
        },
    )

    assert created.status_code == 201
    created_data = created.json()["data"]
    environment_id = UUID(created_data["id"])
    assert created_data["name"] == "Production"
    assert created_data["slug"] == "production"
    assert created_data["environment_type"] == "production"

    listed = client.get(collection_url)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [str(environment_id)]

    detail_url = f"{collection_url}/{environment_id}"
    fetched = client.get(detail_url)
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == str(environment_id)

    updated = client.put(
        detail_url,
        json={
            "name": "Staging",
            "environment_type": "staging",
            "description": "Staging environment",
            "configuration": {"region": "us"},
            "version": 2,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Staging"
    assert updated.json()["data"]["version"] == 2

    deleted = client.delete(detail_url)
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Environment deleted successfully"
    assert environment_id not in repository.environments
    assert client.get(detail_url).status_code == 404


def test_environment_routes_reject_unknown_project_and_mismatched_parent() -> None:
    project_id = uuid4()
    other_project_id = uuid4()
    client, repository = build_test_client(project_id)
    environment_id = uuid4()
    now = datetime.now(UTC)
    repository.environments[environment_id] = Environment(
        entity_id=environment_id,
        project_id=project_id,
        name=EnvironmentName("Production"),
        environment_type=EnvironmentType.PRODUCTION,
        description=None,
        configuration=None,
        created_at=now,
        updated_at=now,
    )

    unknown_project_response = client.get(f"/projects/{other_project_id}/environments")
    mismatched_parent_response = client.get(
        f"/projects/{other_project_id}/environments/{environment_id}"
    )

    assert unknown_project_response.status_code == 404
    assert mismatched_parent_response.status_code == 404
