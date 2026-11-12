from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.domain.identity.entities.session import Session
from app.domain.identity.exceptions import InvalidSession
from app.domain.identity.value_objects.token_hash import TokenHash


def make_session() -> Session:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    return Session(
        entity_id=uuid4(),
        user_id=uuid4(),
        client_device_id=uuid4(),
        token_hash=TokenHash("sha256:session-verifier"),
        expires_at=created_at + timedelta(hours=1),
        created_at=created_at,
    )


def test_new_session_is_active_until_expiration() -> None:
    session = make_session()

    assert session.is_active(session.created_at)
    assert not session.is_active(session.expires_at)


def test_revoking_session_deactivates_it_and_is_idempotent() -> None:
    session = make_session()
    revoked_at = session.created_at + timedelta(minutes=10)

    session.revoke(revoked_at)
    session.revoke(revoked_at + timedelta(minutes=1))

    assert not session.is_active(revoked_at)
    assert session.revoked_at == revoked_at


def test_session_expiration_must_follow_creation() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)

    with pytest.raises(InvalidSession):
        Session(
            entity_id=uuid4(),
            user_id=uuid4(),
            client_device_id=uuid4(),
            token_hash=TokenHash("sha256:session-verifier"),
            expires_at=created_at,
            created_at=created_at,
        )


def test_session_rejects_naive_timestamps() -> None:
    created_at = datetime(2026, 1, 1)

    with pytest.raises(InvalidSession):
        Session(
            entity_id=uuid4(),
            user_id=uuid4(),
            client_device_id=uuid4(),
            token_hash=TokenHash("sha256:session-verifier"),
            expires_at=created_at + timedelta(hours=1),
            created_at=created_at,
        )


def test_session_requires_client_device() -> None:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)

    with pytest.raises(InvalidSession, match="associated with a client device"):
        Session(
            entity_id=uuid4(),
            user_id=uuid4(),
            client_device_id=None,
            token_hash=TokenHash("sha256:session-verifier"),
            expires_at=created_at + timedelta(hours=1),
            created_at=created_at,
        )
