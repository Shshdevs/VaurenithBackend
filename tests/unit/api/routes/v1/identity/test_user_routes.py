from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
from tests.support_jwt import TEST_ISSUER, TEST_PUBLIC_KEY, make_access_token

from app.api.middleware.error_handler import register_error_handlers
from app.api.routes.v1.identity.user import build_user_router
from app.application.identity.dto import VerifiedIdentity
from app.application.identity.use_cases import VerifyIdentityToken
from app.domain.identity import EmailAddress, TokenHash
from app.infrastructure.integrations.identity import JwtAccessTokenVerifier


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
    assert response.json()["code"] == "DELETED"
    assert response.json()["entity_type"] == "user"
    assert delete_user.deleted_user_id == identity.user_id


def test_rejected_registration_token_does_not_create_user() -> None:
    class FakeCreateUser:
        called = False

        async def execute(self, **_kwargs) -> None:
            self.called = True

    create_user = FakeCreateUser()
    token = make_access_token({"iss": "https://wrong.test"})
    verifier = VerifyIdentityToken(
        JwtAccessTokenVerifier(
            public_key=TEST_PUBLIC_KEY,
            issuer=TEST_ISSUER,
            audience="vaurenith-backend-test",
            clock_skew_seconds=2,
            max_lifetime_seconds=600,
        )
    )

    def provide_create_user() -> FakeCreateUser:
        return create_user

    def reject_identity() -> VerifiedIdentity:
        return verifier.execute(token)

    app = FastAPI()
    app.include_router(
        build_user_router(
            get_current_user_dependency=provide_create_user,
            delete_user_dependency=provide_create_user,
            create_user_dependency=provide_create_user,
            revoke_session_dependency=provide_create_user,
            authenticated_identity_dependency=reject_identity,
            verified_identity_dependency=reject_identity,
        )
    )
    register_error_handlers(app)

    response = TestClient(app).post(
        "/users/create",
        json={
            "email": "user@example.test",
            "device_name": "Test device",
            "platform": "other",
        },
        headers={"Authorization": "Bearer rejected"},
    )

    assert response.status_code == 401
    assert create_user.called is False
