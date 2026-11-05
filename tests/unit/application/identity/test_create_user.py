from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from app.application.identity.dto.verified_identity import VerifiedIdentity
from app.application.identity.exceptions import InvalidIdentity
from app.application.identity.use_cases.create_user import CreateUser
from app.domain.identity.entities.session import Session
from app.domain.identity.entities.user import User
from app.domain.identity.value_objects.email import EmailAddress
from app.domain.identity.value_objects.token_hash import TokenHash


class FakeUserRepository:
    def __init__(self) -> None:
        self.registered: tuple[User, Session] | None = None

    async def get_by_id(self, user_id: UUID) -> User | None:
        return None

    async def register(self, user: User, session: Session) -> None:
        self.registered = (user, session)


def make_identity(email: str = "user@example.com") -> VerifiedIdentity:
    now = datetime.now(UTC)
    return VerifiedIdentity(
        user_id=uuid4(),
        email=EmailAddress(email),
        auth_provider="example-idp",
        expires_at=now + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


@pytest.mark.anyio
async def test_create_user_registers_user_and_session() -> None:
    identity = make_identity()
    repository = FakeUserRepository()
    use_case = CreateUser(repository)

    result = await use_case.execute(
        identity=identity,
        email=" user@example.com ",
        display_name="Test User",
    )

    assert result.id == identity.user_id
    assert result.email == "user@example.com"
    assert result.display_name == "Test User"
    assert result.auth_provider == "example-idp"
    assert repository.registered is not None

    user, session = repository.registered
    assert user.id == identity.user_id
    assert user.email == identity.email
    assert session.user_id == identity.user_id
    assert session.token_hash == identity.token_hash
    assert session.expires_at == identity.expires_at
    assert user.created_at == user.updated_at == session.created_at


@pytest.mark.anyio
async def test_create_user_rejects_email_that_differs_from_identity() -> None:
    repository = FakeUserRepository()
    use_case = CreateUser(repository)

    with pytest.raises(InvalidIdentity, match="Email does not match verified identity"):
        await use_case.execute(
            identity=make_identity(),
            email="different@example.com",
            display_name=None,
        )

    assert repository.registered is None


@pytest.mark.anyio
async def test_create_user_rejects_invalid_email() -> None:
    repository = FakeUserRepository()
    use_case = CreateUser(repository)

    with pytest.raises(InvalidIdentity, match="Email does not match verified identity"):
        await use_case.execute(
            identity=make_identity(),
            email="not-an-email",
            display_name=None,
        )

    assert repository.registered is None
