from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpRecordChange

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.projects.project import build_project_route
from app.application.identity import VerifiedIdentity
from app.application.projects.use_cases.projects.update_project import UpdateProject
from app.domain.identity import EmailAddress, TokenHash
from app.domain.projects import Project, ProjectName, ProjectStatus, ProjectType


class FakeProjectRepository:
    def __init__(self, project: Project) -> None:
        self.project = project
        self.updated_project: Project | None = None
        self.expected_version: int | None = None

    async def get_by_id(self, user_id: UUID, project_id: UUID) -> Project | None:
        if self.project.user_id != user_id or self.project.id != project_id:
            return None
        return self.project

    async def update(self, user_id: UUID, project: Project, expected_version: int) -> bool:
        self.updated_project = project
        self.expected_version = expected_version
        return True


def build_test_client(project_version: int = 1) -> tuple[TestClient, FakeProjectRepository]:
    user_id = uuid4()
    project_id = uuid4()
    now = datetime.now(UTC)
    identity = VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress("project-owner@example.test"),
        auth_provider="test-provider",
        expires_at=now + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )
    project = Project(
        entity_id=project_id,
        user_id=user_id,
        name=ProjectName("Original project"),
        created_at=now,
        updated_at=now,
        project_type=ProjectType.SOFTWARE,
        status=ProjectStatus.ACTIVE,
        version=project_version,
    )
    repository = FakeProjectRepository(project)
    update_project = UpdateProject(repository, NoOpRecordChange())

    def unused_dependency() -> None:
        return None

    def provide_update_project() -> UpdateProject:
        return update_project

    def provide_identity() -> VerifiedIdentity:
        return identity

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_project_route(
            create_project_dependency=unused_dependency,
            get_project_dependency=unused_dependency,
            get_user_projects_dependency=unused_dependency,
            update_project_dependency=provide_update_project,
            delete_project_dependency=unused_dependency,
            authenticated_identity_dependency=provide_identity,
        )
    )
    return TestClient(app), repository


def test_put_project_route_updates_project_and_returns_incremented_version() -> None:
    client, repository = build_test_client()
    project_id = repository.project.id

    response = client.put(
        f"/projects/{project_id}",
        json={
            "name": "Updated project",
            "project_type": "fullstack",
            "status": "archived",
            "version": 1,
            "description": "Updated description",
            "metadata": {"environment": "production"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Project updated successfully"
    assert body["data"]["id"] == str(project_id)
    assert body["data"]["name"] == "Updated project"
    assert body["data"]["slug"] == "updated-project"
    assert body["data"]["project_type"] == "fullstack"
    assert body["data"]["status"] == "archived"
    assert body["data"]["version"] == 2
    assert repository.updated_project is not None
    assert repository.updated_project.status is ProjectStatus.ARCHIVED
    assert repository.expected_version == 1


def test_put_project_route_returns_conflict_for_stale_version() -> None:
    client, repository = build_test_client(project_version=3)

    response = client.put(
        f"/projects/{repository.project.id}",
        json={
            "name": "Stale update",
            "project_type": "software",
            "status": "active",
            "version": 2,
        },
    )

    assert response.status_code == 409
    assert "current version is 3" in response.json()["message"]
    assert repository.updated_project is None
