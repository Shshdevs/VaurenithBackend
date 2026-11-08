from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.v1.projects.project import build_project_route
from app.application.identity import VerifiedIdentity
from app.application.projects.use_cases.projects.update_project import UpdateProject
from app.domain.identity import EmailAddress, TokenHash
from app.domain.projects import Project, ProjectName, ProjectStatus, ProjectType


class FakeProjectRepository:
    def __init__(self, project: Project) -> None:
        self.project = project
        self.updated_project: Project | None = None

    async def get_by_id(self, user_id: UUID, project_id: UUID) -> Project | None:
        if self.project.user_id != user_id or self.project.id != project_id:
            return None
        return self.project

    async def update(self, user_id: UUID, project: Project) -> bool:
        self.updated_project = project
        return True


def test_put_project_route_updates_project_and_returns_api_data() -> None:
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
    existing_project = Project(
        entity_id=project_id,
        user_id=user_id,
        name=ProjectName("Original project"),
        created_at=now,
        updated_at=now,
        project_type=ProjectType.SOFTWARE,
        status=ProjectStatus.ACTIVE,
    )
    repository = FakeProjectRepository(existing_project)
    update_project = UpdateProject(repository)

    def unused_dependency() -> None:
        return None

    def provide_update_project() -> UpdateProject:
        return update_project

    def provide_identity() -> VerifiedIdentity:
        return identity

    app = FastAPI()
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

    response = TestClient(app).put(
        f"/projects/{project_id}",
        json={
            "name": "Updated project",
            "project_type": "fullstack",
            "status": "archived",
            "version": 2,
            "description": "Updated description",
            "metadata": {"environment": "production"},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Project updated successfully"
    assert body["data"]["id"] == str(project_id)
    assert body["data"]["user_id"] == str(user_id)
    assert body["data"]["name"] == "Updated project"
    assert body["data"]["slug"] == "updated-project"
    assert body["data"]["project_type"] == "fullstack"
    assert body["data"]["status"] == "archived"
    assert body["data"]["version"] == 2
    assert repository.updated_project is not None
    assert repository.updated_project.status is ProjectStatus.ARCHIVED
