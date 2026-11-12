from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.v1.identity.client_device import build_client_device_router
from app.application.identity.dto import (
    ClientDeviceData,
    SessionData,
    VerifiedIdentity,
)
from app.domain.identity import ClientDeviceStatus, EmailAddress, PlatformType, TokenHash
from app.main import create_app


class FakeUseCase:
    def __init__(self, result) -> None:
        self.result = result

    async def execute(self, *args, **kwargs):
        return self.result


def make_identity() -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_device_data() -> ClientDeviceData:
    return ClientDeviceData(
        id=uuid4(),
        name="Laptop",
        platform=PlatformType.MACOS.value,
        app_version="1.0",
        status=ClientDeviceStatus.ACTIVE.value,
        registered_at=datetime.now(UTC),
        last_seen_at=None,
        revoked_at=None,
    )


def make_app(device_result, session_result) -> FastAPI:
    app = FastAPI()
    identity = make_identity()

    def provide_use_case():
        return FakeUseCase(device_result)

    def provide_session_use_case():
        return FakeUseCase(session_result)

    def provide_identity():
        return identity

    app.include_router(
        build_client_device_router(
            register_client_device_dependency=provide_use_case,
            list_client_devices_dependency=provide_use_case,
            get_client_device_dependency=provide_use_case,
            update_client_device_dependency=provide_use_case,
            create_device_session_dependency=provide_session_use_case,
            list_device_sessions_dependency=provide_session_use_case,
            set_client_device_status_dependency=provide_use_case,
            revoke_client_device_dependency=provide_use_case,
            authenticated_identity_dependency=provide_identity,
            verified_identity_dependency=provide_identity,
        )
    )
    return app


def test_client_device_api_contracts_do_not_expose_token_material() -> None:
    device = make_device_data()
    session = SessionData(
        id=uuid4(),
        client_device_id=device.id,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        revoked_at=None,
    )
    client = TestClient(make_app(device, [session]))

    response = client.get(f"/users/me/devices/{device.id}/sessions")

    assert response.status_code == 200
    body = response.json()
    assert body["entity_type"] == "session"
    serialized = response.text.lower()
    assert "token_hash" not in serialized
    assert "authorization" not in serialized
    assert "bearer" not in serialized
    assert "client_device_id" in body["data"][0]


def test_device_enrollment_uses_server_response_fields_and_rejects_owner_input() -> None:
    device = make_device_data()
    client = TestClient(make_app(device, None))

    response = client.post(
        "/users/me/devices",
        json={"name": "Laptop", "platform": "macos", "user_id": str(uuid4())},
    )

    assert response.status_code == 422


def test_client_device_routes_are_registered() -> None:
    device = make_device_data()
    session = SessionData(
        id=uuid4(),
        client_device_id=device.id,
        created_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        revoked_at=None,
    )
    paths = make_app(device, session).openapi()["paths"]

    assert "/users/me/devices" in paths
    assert "/users/me/devices/{device_id}" in paths
    assert "/users/me/devices/{device_id}/sessions" in paths
    assert "/users/me/devices/{device_id}/status" in paths


def test_redoc_identity_tag_group_includes_client_device_operations() -> None:
    client = TestClient(create_app())
    docs_response = client.get("/docs")
    response = client.get("/openapi.json")
    schema = response.json()
    identity_group = next(
        group for group in schema["x-tagGroups"] if group["name"] == "identity"
    )

    assert docs_response.status_code == 200
    assert response.status_code == 200
    assert "client devices" in identity_group["tags"]
    assert "client devices" in schema["paths"]["/api/v1/users/me/devices"]["post"]["tags"]
