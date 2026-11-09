from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpRecordChange

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.infrastructure.service import build_service_router
from app.application.common.exceptions import Unauthorized
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.service import (
    CreateService,
    DeleteService,
    GetDeviceServices,
    GetEnvironmentServices,
    GetProjectServices,
    GetService,
    GetUserServices,
    UpdateService,
    UpdateServiceStatus,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import Service


class FakeServiceRepository:
    def __init__(self, user_id: UUID) -> None:
        self.user_id = user_id
        self.device_id = uuid4()
        self.project_id = uuid4()
        self.environment_id = uuid4()
        self.services: dict[UUID, Service] = {}

    def _owned(self, identity: VerifiedIdentity) -> bool:
        return identity.user_id == self.user_id

    async def get_by_id(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> Service | None:
        return self.services.get(service_id) if self._owned(identity) else None

    async def get_by_user(self, identity: VerifiedIdentity) -> list[Service]:
        return list(self.services.values()) if self._owned(identity) else []

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[Service]:
        if not self._owned(identity) or device_id != self.device_id:
            return []
        return list(self.services.values())

    async def get_by_project(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[Service]:
        if not self._owned(identity) or project_id != self.project_id:
            return []
        return list(self.services.values())

    async def get_by_environment(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[Service]:
        if not self._owned(identity) or environment_id != self.environment_id:
            return []
        return list(self.services.values())

    async def create(self, identity: VerifiedIdentity, service: Service) -> bool:
        if not self._owned(identity) or service.device_id != self.device_id:
            return False
        self.services[service.id] = service
        return True

    async def update(
        self, identity: VerifiedIdentity, service: Service, expected_version: int
    ) -> bool:
        existing = await self.get_by_id(identity, service.id)
        if existing is None or existing.version != expected_version:
            return False
        self.services[service.id] = service
        return True

    async def delete(self, identity: VerifiedIdentity, service_id: UUID) -> bool:
        if await self.get_by_id(identity, service_id) is None:
            return False
        del self.services[service_id]
        return True


def build_test_client(identity_provider=None):
    identity = VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("service-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("e" * 64),
    )
    repository = FakeServiceRepository(identity.user_id)

    def provide_identity() -> VerifiedIdentity:
        if identity_provider is not None:
            return identity_provider()
        return identity

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_service_router(
            create_service_dependency=lambda: CreateService(repository, NoOpRecordChange()),
            get_service_dependency=lambda: GetService(repository),
            get_user_services_dependency=lambda: GetUserServices(repository),
            get_device_services_dependency=lambda: GetDeviceServices(repository),
            get_project_services_dependency=lambda: GetProjectServices(repository),
            get_environment_services_dependency=lambda: GetEnvironmentServices(repository),
            update_service_dependency=lambda: UpdateService(repository, NoOpRecordChange()),
            update_service_status_dependency=lambda: UpdateServiceStatus(
                repository, NoOpRecordChange()
            ),
            delete_service_dependency=lambda: DeleteService(repository, NoOpRecordChange()),
            authenticated_identity_dependency=provide_identity,
        )
    )
    return TestClient(app), repository


def test_service_routes_support_crud_status_and_parent_lists() -> None:
    client, repository = build_test_client()
    created = client.post(
        "/services",
        json={
            "device_id": str(repository.device_id),
            "project_id": str(repository.project_id),
            "environment_id": str(repository.environment_id),
            "name": " api ",
            "service_type": "application",
            "system_identifier": " systemd:api ",
            "metadata": {"port": 8080},
        },
    )

    assert created.status_code == 201
    data = created.json()["data"]
    service_id = UUID(data["id"])
    assert data["name"] == "api"
    assert data["system_identifier"] == "systemd:api"
    assert data["version"] == 1

    assert client.get(f"/services/{service_id}").status_code == 200
    assert len(client.get("/services").json()["data"]) == 1
    assert len(client.get(f"/devices/{repository.device_id}/services").json()["data"]) == 1
    assert (
        len(client.get(f"/projects/{repository.project_id}/services").json()["data"]) == 1
    )
    assert (
        len(
            client.get(f"/environments/{repository.environment_id}/services").json()["data"]
        )
        == 1
    )

    updated = client.put(
        f"/services/{service_id}",
        json={
            "device_id": str(repository.device_id),
            "project_id": str(repository.project_id),
            "environment_id": str(repository.environment_id),
            "name": "api-v2",
            "service_type": "application",
            "version": 1,
            "metadata": {"port": 8081},
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["version"] == 2

    status_update = client.patch(
        f"/services/{service_id}/status", json={"status": "running", "version": 2}
    )
    assert status_update.status_code == 200
    assert status_update.json()["data"]["status"] == "running"
    assert status_update.json()["data"]["version"] == 3
    assert (
        client.put(
            f"/services/{service_id}",
            json={
                "device_id": str(repository.device_id),
                "name": "stale",
                "service_type": "application",
                "version": 2,
            },
        ).status_code
        == 409
    )

    assert client.delete(f"/services/{service_id}").status_code == 200
    assert client.get(f"/services/{service_id}").status_code == 404


def test_service_routes_reject_invalid_input_and_authentication() -> None:
    def reject_identity() -> VerifiedIdentity:
        raise Unauthorized("Authentication required")

    unauthenticated, _ = build_test_client(reject_identity)
    assert unauthenticated.get("/services/" + str(uuid4())).status_code == 401

    client, repository = build_test_client()
    invalid = client.post(
        "/services",
        json={
            "device_id": str(repository.device_id),
            "name": " ",
            "service_type": "application",
        },
    )
    assert invalid.status_code == 422
