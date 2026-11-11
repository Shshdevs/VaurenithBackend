from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpRecordChange, NoOpUnitOfWork
from tests.support_containers import (
    FakeContainerRepository,
    add_owned_container_associations,
    make_container_identity,
)

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.infrastructure.container import build_container_router
from app.application.common.exceptions import Unauthorized
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.container import (
    CreateContainer,
    DeleteContainer,
    GetContainer,
    GetContainersByProject,
    GetDeviceContainers,
    GetEnvironmentContainers,
    GetServiceContainers,
    GetUserContainers,
    UpdateContainer,
)
from app.domain.infrastructure.enums import ContainerStatus


def build_test_client(identity_provider=None):
    identity = make_container_identity()
    repository = FakeContainerRepository()
    device_id, project_id, environment_id, service_id = add_owned_container_associations(
        repository, identity
    )

    def provide_identity() -> VerifiedIdentity:
        if identity_provider is not None:
            return identity_provider()
        return identity

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_container_router(
            create_container_dependency=lambda: CreateContainer(
                repository, NoOpRecordChange(), NoOpUnitOfWork()
            ),
            get_container_dependency=lambda: GetContainer(repository),
            get_user_containers_dependency=lambda: GetUserContainers(repository),
            get_device_containers_dependency=lambda: GetDeviceContainers(repository),
            get_project_containers_dependency=lambda: GetContainersByProject(repository),
            get_environment_containers_dependency=lambda: GetEnvironmentContainers(
                repository
            ),
            get_service_containers_dependency=lambda: GetServiceContainers(repository),
            update_container_dependency=lambda: UpdateContainer(
                repository, NoOpRecordChange(), NoOpUnitOfWork()
            ),
            delete_container_dependency=lambda: DeleteContainer(
                repository, NoOpRecordChange(), NoOpUnitOfWork()
            ),
            authenticated_identity_dependency=provide_identity,
        )
    )
    return (
        TestClient(app),
        repository,
        device_id,
        project_id,
        environment_id,
        service_id,
    )


def test_container_routes_support_crud_and_parent_lists() -> None:
    client, _, device_id, project_id, environment_id, service_id = build_test_client()
    created = client.post(
        "/containers",
        json={
            "device_id": str(device_id),
            "project_id": str(project_id),
            "environment_id": str(environment_id),
            "service_id": str(service_id),
            "container_runtime_id": " docker:api-123 ",
            "name": " api ",
            "image": " example/api:1.0 ",
            "ports": {"8080/tcp": [8080]},
        },
    )

    assert created.status_code == 201
    data = created.json()["data"]
    container_id = UUID(data["id"])
    assert data["name"] == "api"
    assert data["container_runtime_id"] == "docker:api-123"
    assert data["image"] == "example/api:1.0"
    assert data["status"] == "unknown"
    assert data["version"] == 1

    assert client.get(f"/containers/{container_id}").status_code == 200
    assert len(client.get("/containers").json()["data"]) == 1
    assert len(client.get(f"/devices/{device_id}/containers").json()["data"]) == 1
    assert len(client.get(f"/projects/{project_id}/containers").json()["data"]) == 1
    assert len(client.get(f"/environments/{environment_id}/containers").json()["data"]) == 1
    assert len(client.get(f"/services/{service_id}/containers").json()["data"]) == 1

    updated = client.put(
        f"/containers/{container_id}",
        json={
            "version": 1,
            "device_id": str(device_id),
            "project_id": str(project_id),
            "environment_id": str(environment_id),
            "service_id": str(service_id),
            "container_runtime_id": "docker:api-123",
            "name": "api-v2",
            "status": "running",
            "image": "example/api:2.0",
            "ports": {"8080/tcp": [8080]},
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["version"] == 2
    assert updated.json()["data"]["name"] == "api-v2"
    assert updated.json()["data"]["status"] == "running"

    stale_update = client.put(
        f"/containers/{container_id}",
        json={
            "version": 1,
            "device_id": str(device_id),
            "container_runtime_id": "docker:api-123",
            "name": "stale",
            "status": "running",
        },
    )
    assert stale_update.status_code == 409

    assert client.delete(f"/containers/{container_id}").status_code == 200
    assert client.get(f"/containers/{container_id}").status_code == 404


def test_container_routes_reject_invalid_input_and_authentication() -> None:
    def reject_identity() -> VerifiedIdentity:
        raise Unauthorized("Authentication required")

    unauthenticated, *_ = build_test_client(reject_identity)
    assert unauthenticated.get("/containers").status_code == 401

    client, _, device_id, *_ = build_test_client()
    invalid = client.post(
        "/containers",
        json={
            "device_id": str(device_id),
            "container_runtime_id": " ",
            "name": "api",
            "status": ContainerStatus.RUNNING.value,
        },
    )
    assert invalid.status_code == 422
