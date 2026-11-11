from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpRecordChange, NoOpUnitOfWork
from tests.support_connections import FakeConnectionRepository

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.infrastructure.connection import build_connection_router
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.connection import (
    CreateConnection,
    DeleteConnection,
    GetConnection,
    GetDeviceConnections,
    GetUserConnections,
    ReportConnectionStatus,
    UpdateConnection,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure.enums import ConnectionStatus


def build_test_client() -> tuple[TestClient, FakeConnectionRepository, UUID]:
    identity = VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("connection-owner@example.test"),
        auth_provider="connection-route-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )
    device_id = uuid4()
    repository = FakeConnectionRepository({device_id: identity.user_id})

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_connection_router(
            create_connection_dependency=lambda: CreateConnection(
                repository, NoOpRecordChange(), NoOpUnitOfWork()
            ),
            get_connection_dependency=lambda: GetConnection(repository),
            get_user_connections_dependency=lambda: GetUserConnections(repository),
            get_device_connections_dependency=lambda: GetDeviceConnections(repository),
            update_connection_dependency=lambda: UpdateConnection(
                repository, NoOpRecordChange(), NoOpUnitOfWork()
            ),
            report_connection_status_dependency=lambda: ReportConnectionStatus(
                repository, NoOpRecordChange(), NoOpUnitOfWork()
            ),
            delete_connection_dependency=lambda: DeleteConnection(
                repository, NoOpRecordChange(), NoOpUnitOfWork()
            ),
            authenticated_identity_dependency=lambda: identity,
        )
    )
    return TestClient(app), repository, device_id


def test_connection_routes_cover_crud_status_and_device_listing() -> None:
    client, _, device_id = build_test_client()
    created_response = client.post(
        "/connections",
        json={
            "device_id": str(device_id),
            "name": "Primary SSH",
            "host": "server.example.test",
            "port": 22,
            "username": "admin",
            "authentication_type": "ssh_key",
            "is_default": True,
        },
    )

    assert created_response.status_code == 201
    created = created_response.json()["data"]
    connection_id = UUID(created["id"])
    assert created["slug"] == "primary-ssh"
    assert created["version"] == 1
    assert "last_error" not in created
    assert client.get("/connections").status_code == 200
    assert client.get(f"/connections/{connection_id}").status_code == 200
    assert len(client.get(f"/devices/{device_id}/connections").json()["data"]) == 1

    updated_response = client.put(
        f"/connections/{connection_id}",
        json={
            "version": 1,
            "name": "Production SSH",
            "host": "ssh.example.test",
            "port": 2222,
            "username": "deploy",
            "authentication_type": "agent",
            "connection_timeout": 45,
            "is_default": True,
        },
    )
    assert updated_response.status_code == 200
    assert updated_response.json()["data"]["version"] == 2

    status_response = client.patch(
        f"/connections/{connection_id}/status",
        json={
            "version": 2,
            "status": "failed",
            "last_error": "private diagnostic detail",
        },
    )
    assert status_response.status_code == 200
    assert status_response.json()["data"]["last_status"] == ConnectionStatus.FAILED.value
    assert "last_error" not in status_response.json()["data"]

    assert client.delete(f"/connections/{connection_id}").status_code == 200
    assert client.get(f"/connections/{connection_id}").status_code == 404


def test_connection_routes_validate_fields_and_hide_foreign_devices() -> None:
    client, _, _ = build_test_client()
    invalid = client.post(
        "/connections",
        json={
            "device_id": str(uuid4()),
            "name": " ",
            "host": "",
            "username": "admin",
            "authentication_type": "password",
        },
    )
    assert invalid.status_code == 422
    assert client.get(f"/devices/{uuid4()}/connections").json()["data"] == []

    missing_device_connection = client.post(
        "/connections",
        json={
            "device_id": str(uuid4()),
            "name": "Private connection",
            "host": "server.example.test",
            "username": "admin",
            "authentication_type": "password",
        },
    )
    assert missing_device_connection.status_code == 404
