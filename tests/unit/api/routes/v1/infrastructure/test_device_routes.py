from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support import NoOpRecordChange

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.infrastructure.device import build_device_router
from app.application.common.exceptions import Unauthorized
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.device import (
    CreateDevice,
    DeleteDevice,
    GetDevice,
    GetUserDevices,
    UpdateDevice,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import Device


class FakeDeviceRepository:
    def __init__(self) -> None:
        self.devices: dict[UUID, Device] = {}
        self.deleted: set[UUID] = set()

    async def get_by_id(self, identity: VerifiedIdentity, device_id: UUID) -> Device | None:
        device = self.devices.get(device_id)
        if (
            device is None
            or device_id in self.deleted
            or device.user_id != identity.user_id
        ):
            return None
        return device

    async def get_by_user(self, identity: VerifiedIdentity) -> list[Device]:
        return [
            device
            for device_id, device in self.devices.items()
            if device.user_id == identity.user_id and device_id not in self.deleted
        ]

    async def create(self, device: Device) -> None:
        self.devices[device.id] = device

    async def update(
        self, identity: VerifiedIdentity, device: Device, expected_version: int
    ) -> bool:
        existing = await self.get_by_id(identity, device.id)
        if existing is None or existing.version != expected_version:
            return False
        self.devices[device.id] = device
        return True

    async def delete(
        self, identity: VerifiedIdentity, device_id: UUID, deleted_at: datetime
    ) -> bool:
        if await self.get_by_id(identity, device_id) is None:
            return False
        self.deleted.add(device_id)
        return True


def make_identity() -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("device-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )


def build_test_client(
    identity_provider=None,
) -> tuple[TestClient, FakeDeviceRepository, VerifiedIdentity]:
    identity = make_identity()
    repository = FakeDeviceRepository()

    def provide_identity() -> VerifiedIdentity:
        if identity_provider is not None:
            return identity_provider()
        return identity

    def provide_create() -> CreateDevice:
        return CreateDevice(repository, NoOpRecordChange())

    def provide_get() -> GetDevice:
        return GetDevice(repository)

    def provide_list() -> GetUserDevices:
        return GetUserDevices(repository)

    def provide_update() -> UpdateDevice:
        return UpdateDevice(repository, NoOpRecordChange())

    def provide_delete() -> DeleteDevice:
        return DeleteDevice(repository, NoOpRecordChange())

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_device_router(
            create_device_dependency=provide_create,
            get_device_dependency=provide_get,
            get_user_devices_dependency=provide_list,
            update_device_dependency=provide_update,
            delete_device_dependency=provide_delete,
            authenticated_identity_dependency=provide_identity,
        )
    )
    return TestClient(app), repository, identity


def test_device_routes_support_create_list_get_update_and_soft_delete() -> None:
    client, repository, identity = build_test_client()

    created = client.post(
        "/devices",
        json={
            "name": " worker-01 ",
            "device_type": "vps",
            "operating_system": " Linux ",
            "os_version": " 6.1 ",
            "architecture": " x86_64 ",
            "tags": [" production "],
        },
    )

    assert created.status_code == 201
    data = created.json()["data"]
    device_id = UUID(data["id"])
    assert data["user_id"] == str(identity.user_id)
    assert data["name"] == "worker-01"
    assert data["slug"] == "worker-01"
    assert data["operating_system"] == "Linux"
    assert data["tags"] == ["production"]

    listed = client.get("/devices")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["data"]] == [str(device_id)]

    fetched = client.get(f"/devices/{device_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == str(device_id)

    updated = client.put(
        f"/devices/{device_id}",
        json={
            "name": "worker-02",
            "device_type": "cloud",
            "tags": ["staging"],
            "version": data["version"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "worker-02"
    assert updated.json()["data"]["version"] == data["version"] + 1

    deleted = client.delete(f"/devices/{device_id}")
    assert deleted.status_code == 200
    assert deleted.json()["data"] is None
    assert device_id in repository.deleted
    assert client.get(f"/devices/{device_id}").status_code == 404


def test_device_routes_enforce_authentication_owner_scope_and_input_validation() -> None:
    def reject_identity() -> VerifiedIdentity:
        raise Unauthorized("Authentication required")

    unauthenticated, _, _ = build_test_client(reject_identity)
    assert unauthenticated.get("/devices").status_code == 401

    client, repository, _ = build_test_client()
    invalid_name = client.post("/devices", json={"name": "  ", "device_type": "vps"})
    assert invalid_name.status_code == 422
    supplied_owner = client.post(
        "/devices",
        json={"name": "worker", "device_type": "vps", "user_id": str(uuid4())},
    )
    assert supplied_owner.status_code == 422

    created = client.post("/devices", json={"name": "private", "device_type": "vps"})
    device_id = UUID(created.json()["data"]["id"])
    device = repository.devices[device_id]
    other_owner_device = Device(
        entity_id=device.id,
        user_id=uuid4(),
        name=device.name_value,
        created_at=device.created_at,
        updated_at=device.updated_at,
        device_type=device.device_type,
    )
    repository.devices[device_id] = other_owner_device
    assert client.get(f"/devices/{device_id}").status_code == 404
