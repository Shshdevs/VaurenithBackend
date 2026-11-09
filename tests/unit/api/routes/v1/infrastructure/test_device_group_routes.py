from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.infrastructure.device_group import build_device_group_router
from app.application.common.exceptions import Unauthorized
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.use_cases.device_group import (
    CreateDeviceGroup,
    DeleteDeviceGroup,
    GetDeviceGroup,
    UpdateDeviceGroup,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import DeviceGroup


class FakeDeviceGroupRepository:
    def __init__(self) -> None:
        self.groups: dict[UUID, DeviceGroup] = {}

    async def get_by_id(
        self, identity: VerifiedIdentity, device_group_id: UUID
    ) -> DeviceGroup | None:
        group = self.groups.get(device_group_id)
        return group if group and group.user_id == identity.user_id else None

    async def create(self, device_group: DeviceGroup) -> None:
        self.groups[device_group.id] = device_group

    async def update(self, identity: VerifiedIdentity, device_group: DeviceGroup) -> bool:
        if await self.get_by_id(identity, device_group.id) is None:
            return False
        self.groups[device_group.id] = device_group
        return True

    async def delete(self, identity: VerifiedIdentity, device_group_id: UUID) -> bool:
        if await self.get_by_id(identity, device_group_id) is None:
            return False
        del self.groups[device_group_id]
        return True


def make_identity() -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("device-group-owner@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("d" * 64),
    )


def build_test_client(
    identity_provider=None,
) -> tuple[TestClient, FakeDeviceGroupRepository, VerifiedIdentity]:
    identity = make_identity()
    repository = FakeDeviceGroupRepository()

    def provide_identity() -> VerifiedIdentity:
        if identity_provider is not None:
            return identity_provider()
        return identity

    def provide_create() -> CreateDeviceGroup:
        return CreateDeviceGroup(repository)

    def provide_get() -> GetDeviceGroup:
        return GetDeviceGroup(repository)

    def provide_update() -> UpdateDeviceGroup:
        return UpdateDeviceGroup(repository)

    def provide_delete() -> DeleteDeviceGroup:
        return DeleteDeviceGroup(repository)

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_device_group_router(
            create_device_group_dependency=provide_create,
            get_device_group_dependency=provide_get,
            update_device_group_dependency=provide_update,
            delete_device_group_dependency=provide_delete,
            authenticated_identity_dependency=provide_identity,
        )
    )
    return TestClient(app), repository, identity


def test_device_group_routes_support_create_get_update_and_delete() -> None:
    client, repository, identity = build_test_client()

    created = client.post(
        "/device-groups",
        json={"name": "  Production  ", "description": "  Servers  "},
    )

    assert created.status_code == 201
    created_data = created.json()["data"]
    group_id = UUID(created_data["id"])
    assert created_data["user_id"] == str(identity.user_id)
    assert created_data["name"] == "Production"
    assert created_data["slug"] == "production"

    fetched = client.get(f"/device-groups/{group_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["id"] == str(group_id)

    updated = client.put(
        f"/device-groups/{group_id}",
        json={"name": "Staging", "description": "Deployment group"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["name"] == "Staging"
    assert updated.json()["data"]["user_id"] == str(identity.user_id)

    deleted = client.delete(f"/device-groups/{group_id}")
    assert deleted.status_code == 200
    assert deleted.json()["data"] is None
    assert group_id not in repository.groups


def test_device_group_routes_enforce_authentication_and_owner_scope() -> None:
    def reject_identity() -> VerifiedIdentity:
        raise Unauthorized("Authentication required")

    unauthenticated_client, _, _ = build_test_client(reject_identity)
    assert unauthenticated_client.get(f"/device-groups/{uuid4()}").status_code == 401

    client, repository, identity = build_test_client()
    other_identity = make_identity()
    response = client.post("/device-groups", json={"name": "Private"})
    group_id = UUID(response.json()["data"]["id"])
    repository.groups[group_id] = DeviceGroup(
        entity_id=group_id,
        user_id=other_identity.user_id,
        name=repository.groups[group_id].name_value,
        created_at=repository.groups[group_id].created_at,
        updated_at=repository.groups[group_id].updated_at,
    )

    assert client.get(f"/device-groups/{group_id}").status_code == 404
    assert identity.user_id != other_identity.user_id


def test_device_group_routes_validate_request_and_forbid_client_owner_id() -> None:
    client, _, _ = build_test_client()

    invalid_name = client.post("/device-groups", json={"name": "  "})
    assert invalid_name.status_code == 422

    supplied_owner = client.post(
        "/device-groups",
        json={"user_id": str(uuid4()), "name": "Private"},
    )
    assert supplied_owner.status_code == 422
