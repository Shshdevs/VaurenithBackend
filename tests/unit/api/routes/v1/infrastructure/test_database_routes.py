from uuid import UUID

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpRecordChange, NoOpUnitOfWork
from tests.support_databases import (
    FakeDatabaseRepository,
    add_owned_database_associations,
    make_database_identity,
)

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.infrastructure.database import build_database_router
from app.application.common.exceptions import Unauthorized
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.database import (
    CreateDatabase,
    DeleteDatabase,
    GetDatabase,
    GetDatabasesByContainer,
    GetDatabasesByDevice,
    GetDatabasesByEnvironment,
    GetDatabasesByProject,
    GetDatabasesByService,
    GetUserDatabases,
    UpdateDatabase,
)


def build_test_client(identity_provider=None):
    identity = make_database_identity()
    repository = FakeDatabaseRepository()
    device_id, project_id, environment_id, container_id, service_id = (
        add_owned_database_associations(repository, identity)
    )

    def provide_identity() -> VerifiedIdentity:
        if identity_provider is not None:
            return identity_provider()
        return identity

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_database_router(
            create_database_dependency=lambda: CreateDatabase(
                repository, NoOpRecordChange(), NoOpUnitOfWork()
            ),
            get_database_dependency=lambda: GetDatabase(repository),
            get_user_databases_dependency=lambda: GetUserDatabases(repository),
            get_device_databases_dependency=lambda: GetDatabasesByDevice(repository),
            get_project_databases_dependency=lambda: GetDatabasesByProject(repository),
            get_environment_databases_dependency=lambda: GetDatabasesByEnvironment(
                repository
            ),
            get_container_databases_dependency=lambda: GetDatabasesByContainer(repository),
            get_service_databases_dependency=lambda: GetDatabasesByService(repository),
            update_database_dependency=lambda: UpdateDatabase(
                repository, NoOpRecordChange(), NoOpUnitOfWork()
            ),
            delete_database_dependency=lambda: DeleteDatabase(
                repository, NoOpRecordChange(), NoOpUnitOfWork()
            ),
            authenticated_identity_dependency=provide_identity,
        )
    )
    return (
        TestClient(app),
        device_id,
        project_id,
        environment_id,
        container_id,
        service_id,
    )


def test_database_routes_support_crud_and_association_lists() -> None:
    client, device_id, project_id, environment_id, container_id, service_id = (
        build_test_client()
    )
    created = client.post(
        "/databases",
        json={
            "device_id": str(device_id),
            "project_id": str(project_id),
            "environment_id": str(environment_id),
            "container_id": str(container_id),
            "service_id": str(service_id),
            "name": " primary ",
            "dbms_type": "postgresql",
            "host": " db.internal ",
            "port": 5432,
            "database_name": " app ",
        },
    )

    assert created.status_code == 201
    data = created.json()["data"]
    database_id = UUID(data["id"])
    assert data["name"] == "primary"
    assert data["host"] == "db.internal"
    assert data["database_name"] == "app"
    assert data["status"] == "unknown"
    assert data["version"] == 1

    assert client.get(f"/databases/{database_id}").status_code == 200
    assert len(client.get("/databases").json()["data"]) == 1
    assert len(client.get(f"/devices/{device_id}/databases").json()["data"]) == 1
    assert len(client.get(f"/projects/{project_id}/databases").json()["data"]) == 1
    assert len(client.get(f"/environments/{environment_id}/databases").json()["data"]) == 1
    assert len(client.get(f"/containers/{container_id}/databases").json()["data"]) == 1
    assert len(client.get(f"/services/{service_id}/databases").json()["data"]) == 1

    updated = client.put(
        f"/databases/{database_id}",
        json={
            "version": 1,
            "device_id": str(device_id),
            "project_id": str(project_id),
            "environment_id": str(environment_id),
            "container_id": str(container_id),
            "service_id": str(service_id),
            "name": "primary-v2",
            "dbms_type": "postgresql",
            "status": "running",
            "host": "db.internal",
            "port": 5433,
            "database_name": "app_v2",
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["version"] == 2
    assert updated.json()["data"]["status"] == "running"

    stale = client.put(
        f"/databases/{database_id}",
        json={
            "version": 1,
            "device_id": str(device_id),
            "name": "stale",
            "dbms_type": "postgresql",
            "status": "running",
        },
    )
    assert stale.status_code == 409

    assert client.delete(f"/databases/{database_id}").status_code == 200
    assert client.get(f"/databases/{database_id}").status_code == 404


def test_database_routes_reject_invalid_input_and_authentication() -> None:
    def reject_identity() -> VerifiedIdentity:
        raise Unauthorized("Authentication required")

    unauthenticated, *_ = build_test_client(reject_identity)
    assert unauthenticated.get("/databases").status_code == 401

    client, device_id, *_ = build_test_client()
    invalid = client.post(
        "/databases",
        json={
            "device_id": str(device_id),
            "name": "main",
            "dbms_type": "postgresql",
            "port": 70000,
        },
    )
    assert invalid.status_code == 422
