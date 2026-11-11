from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.infrastructure.device_group import build_device_group_router
from app.application.identity import VerifiedIdentity
from app.domain.identity import EmailAddress, TokenHash


class FakeGroupMemberUseCase:
    def __init__(self) -> None:
        self.members: dict[tuple[str, str], dict] = {}

    async def list_members(self, identity, group_id):
        return [
            member
            for (stored_group, _), member in self.members.items()
            if stored_group == str(group_id)
        ]

    async def add(self, identity, group_id, device_id):
        key = (str(group_id), str(device_id))
        self.members[key] = {
            "id": str(uuid4()),
            "group_id": str(group_id),
            "device_id": str(device_id),
            "created_at": datetime.now(UTC),
        }
        return self.members[key]

    async def remove(self, identity, group_id, device_id):
        key = (str(group_id), str(device_id))
        self.members.pop(key)


def build_test_client() -> tuple[TestClient, FakeGroupMemberUseCase]:
    identity = VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("group-members@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )
    use_case = FakeGroupMemberUseCase()

    def provide_identity() -> VerifiedIdentity:
        return identity

    def provide_use_case() -> FakeGroupMemberUseCase:
        return use_case

    app = FastAPI()
    register_error_handlers(app)
    app.include_router(
        build_device_group_router(
            create_device_group_dependency=provide_use_case,
            get_device_group_dependency=provide_use_case,
            get_user_device_groups_dependency=provide_use_case,
            get_device_group_members_dependency=provide_use_case,
            add_device_group_member_dependency=provide_use_case,
            remove_device_group_member_dependency=provide_use_case,
            delete_device_group_dependency=provide_use_case,
            update_device_group_dependency=provide_use_case,
            authenticated_identity_dependency=provide_identity,
        )
    )
    return TestClient(app), use_case


def test_device_group_member_routes_add_list_and_remove_members() -> None:
    client, _ = build_test_client()
    group_id, device_id = uuid4(), uuid4()

    added = client.post(
        f"/device-groups/{group_id}/members", json={"device_id": str(device_id)}
    )

    assert added.status_code == 201
    assert added.json()["data"]["group_id"] == str(group_id)
    assert added.json()["data"]["device_id"] == str(device_id)

    listed = client.get(f"/device-groups/{group_id}/members")
    assert listed.status_code == 200
    assert [member["device_id"] for member in listed.json()["data"]] == [str(device_id)]

    removed = client.delete(f"/device-groups/{group_id}/members/{device_id}")
    assert removed.status_code == 200
    assert removed.json()["data"] is None
    assert client.get(f"/device-groups/{group_id}/members").json()["data"] == []
