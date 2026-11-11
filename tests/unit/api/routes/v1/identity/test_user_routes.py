from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes.v1.identity.user import build_user_router
from app.application.identity.dto import VerifiedIdentity
from app.domain.identity import EmailAddress, TokenHash


class FakeDeleteUser:
    def __init__(self) -> None:
        self.deleted_user_id = None

    async def execute(self, user_id) -> None:
        self.deleted_user_id = user_id


def test_delete_me_deletes_authenticated_account() -> None:
    identity = VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("account@example.test"),
        auth_provider="test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )
    delete_user = FakeDeleteUser()

    def provide_dependency() -> FakeDeleteUser:
        return delete_user

    def provide_identity() -> VerifiedIdentity:
        return identity

    app = FastAPI()
    app.include_router(
        build_user_router(
            get_current_user_dependency=provide_dependency,
            delete_user_dependency=provide_dependency,
            create_user_dependency=provide_dependency,
            revoke_session_dependency=provide_dependency,
            authenticated_identity_dependency=provide_identity,
            verified_identity_dependency=provide_identity,
        )
    )

    response = TestClient(app).delete("/users/me")

    assert response.status_code == 200
    assert response.json()["message"] == "User deleted successfully"
    assert delete_user.deleted_user_id == identity.user_id
