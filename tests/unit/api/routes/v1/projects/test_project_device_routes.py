from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.projects.project_device import build_project_device_route
from app.application.common.exceptions import Unauthorized
from app.application.identity import VerifiedIdentity
from app.application.projects.use_cases.project_devices import (
    DeleteProjectDevice,
    GetDeviceProjects,
    GetProjectDevice,
    GetProjectDevices,
    LinkProjectDevice,
    UpdateProjectDevice,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.projects import ProjectDevice


class FakeProjectDeviceRepository:
    def __init__(self) -> None:
        self.project_devices: dict[UUID, ProjectDevice] = {}

    async def get_by_id(self, project_device_id: UUID) -> ProjectDevice | None:
        return self.project_devices.get(project_device_id)

    async def get_by_project(self, project_id: UUID) -> list[ProjectDevice]:
        return [
            item for item in self.project_devices.values() if item.project_id == project_id
        ]

    async def get_by_device(self, device_id: UUID) -> list[ProjectDevice]:
        return [
            item for item in self.project_devices.values() if item.device_id == device_id
        ]

    async def link(self, project_device: ProjectDevice) -> None:
        self.project_devices[project_device.id] = project_device

    async def update(self, project_device: ProjectDevice) -> bool:
        if project_device.id not in self.project_devices:
            return False
        self.project_devices[project_device.id] = project_device
        return True

    async def delete(self, project_device_id: UUID) -> bool:
        return self.project_devices.pop(project_device_id, None) is not None


class FakeProjectRepository:
    def __init__(self, projects: dict[UUID, UUID]) -> None:
        self.projects = projects

    async def get_by_id(self, user_id: UUID, project_id: UUID) -> object | None:
        if self.projects.get(project_id) != user_id:
            return None
        return type("Project", (), {"id": project_id})()

    async def get_user_projects(self, user_id: UUID) -> list[object]:
        return [
            type("Project", (), {"id": project_id})()
            for project_id, owner_id in self.projects.items()
            if owner_id == user_id
        ]


def make_identity() -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("project-device-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )


def build_test_client(
    identity_provider: Callable[[], VerifiedIdentity] | None = None,
) -> tuple[TestClient, FakeProjectDeviceRepository, VerifiedIdentity, UUID]:
    identity = make_identity()
    project_id = uuid4()
    repository = FakeProjectDeviceRepository()
    project_repository = FakeProjectRepository({project_id: identity.user_id})
    project_device_repository = repository

    def provide_identity() -> VerifiedIdentity:
        if identity_provider is not None:
            return identity_provider()
        return identity

    def provide_link() -> LinkProjectDevice:
        return LinkProjectDevice(project_device_repository, project_repository)

    def provide_update() -> UpdateProjectDevice:
        return UpdateProjectDevice(project_device_repository, project_repository)

    def provide_delete() -> DeleteProjectDevice:
        return DeleteProjectDevice(project_device_repository, project_repository)

    def provide_get_device_projects() -> GetDeviceProjects:
        return GetDeviceProjects(project_device_repository, project_repository)

    def provide_get_project_device() -> GetProjectDevice:
        return GetProjectDevice(project_device_repository, project_repository)

    def provide_get_project_devices() -> GetProjectDevices:
        return GetProjectDevices(project_device_repository, project_repository)

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_project_device_route(
            link_project_device_dependency=provide_link,
            get_project_device_dependency=provide_get_project_device,
            get_project_devices_dependency=provide_get_project_devices,
            get_device_projects_dependency=provide_get_device_projects,
            update_project_device_dependency=provide_update,
            delete_project_device_dependency=provide_delete,
            authenticated_identity_dependency=provide_identity,
        )
    )
    return TestClient(app), repository, identity, project_id


def test_project_device_routes_support_link_list_get_update_and_delete() -> None:
    client, repository, identity, project_id = build_test_client()
    device_id = uuid4()

    response = client.post(
        "/project_devices",
        json={"project_id": str(project_id), "device_id": str(device_id), "role": None},
    )

    assert response.status_code == 201
    assert response.json()["data"]["role"] is None
    project_device_id = UUID(response.json()["data"]["id"])
    assert project_device_id in repository.project_devices

    project_devices = client.get(f"/projects/{project_id}/devices")
    assert project_devices.status_code == 200
    assert [item["id"] for item in project_devices.json()["data"]] == [
        str(project_device_id)
    ]

    device_projects = client.get(f"/devices/{device_id}/projects")
    assert device_projects.status_code == 200
    assert [item["project_id"] for item in device_projects.json()["data"]] == [
        str(project_id)
    ]

    detail = client.get(f"/project_devices/{project_device_id}")
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == str(project_device_id)

    updated = client.put(
        f"/project_devices/{project_device_id}",
        json={
            "project_id": str(project_id),
            "device_id": str(device_id),
            "role": "operator",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["role"] == "operator"

    deleted = client.delete(f"/project_devices/{project_device_id}")
    assert deleted.status_code == 200
    assert repository.project_devices == {}


def test_project_device_routes_reject_unauthenticated_and_unowned_requests() -> None:
    def reject_identity() -> VerifiedIdentity:
        raise Unauthorized("Authentication required")

    unauthenticated_client, _, _, project_id = build_test_client(reject_identity)
    response = unauthenticated_client.get(f"/projects/{project_id}/devices")
    assert response.status_code == 401

    client, _, _, project_id = build_test_client()
    response = client.get(f"/projects/{uuid4()}/devices")
    assert response.status_code == 404


def test_project_device_routes_validate_optional_role_values() -> None:
    client, _, _, project_id = build_test_client()
    response = client.post(
        "/project_devices",
        json={"project_id": str(project_id), "device_id": str(uuid4()), "role": " "},
    )
    assert response.status_code == 422
