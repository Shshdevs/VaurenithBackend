from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from tests.support import NoOpUnitOfWork

from app.application.identity import InvalidIdentity, VerifiedIdentity
from app.application.identity.use_cases import RevokeSession
from app.domain.identity import EmailAddress, TokenHash


class FakeSessionRepository:
    def __init__(self, should_revoke: bool = True) -> None:
        self.should_revoke = should_revoke
        self.revoked_token_hash: TokenHash | None = None
        self.revoked_at: datetime | None = None

    async def has_active_session(self, token_hash: TokenHash, at: datetime) -> bool:
        return False

    async def revoke_session(self, token_hash: TokenHash, at: datetime) -> bool:
        self.revoked_token_hash = token_hash
        self.revoked_at = at
        return self.should_revoke


def make_identity() -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress("session-owner@example.test"),
        auth_provider="session-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


@pytest.mark.anyio
async def test_revoke_session_revokes_the_authenticated_token() -> None:
    identity = make_identity()
    repository = FakeSessionRepository()
    use_case = RevokeSession(repository, NoOpUnitOfWork())

    await use_case.execute(identity)

    assert repository.revoked_token_hash == identity.token_hash
    assert repository.revoked_at is not None
    assert repository.revoked_at.tzinfo is UTC


@pytest.mark.anyio
async def test_revoke_session_rejects_a_session_that_is_no_longer_active() -> None:
    repository = FakeSessionRepository(should_revoke=False)
    use_case = RevokeSession(repository, NoOpUnitOfWork())

    with pytest.raises(InvalidIdentity, match="Identity session is inactive"):
        await use_case.execute(make_identity())
