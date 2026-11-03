from datetime import UTC, datetime
from uuid import uuid4

from app.domain.identity.entities.user import User
from app.domain.identity.value_objects.email import EmailAddress


def test_user_exposes_its_values() -> None:
    entity_id = uuid4()
    email = EmailAddress("person@example.com")
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    updated_at = datetime(2026, 1, 2, tzinfo=UTC)

    user = User(
        entity_id=entity_id,
        email=email,
        display_name="Person",
        auth_provider="oauth",
        created_at=created_at,
        updated_at=updated_at,
    )

    assert user.id == entity_id
    assert user.email is email
    assert user.display_name == "Person"
    assert user.auth_provider == "oauth"
    assert user.created_at == created_at
    assert user.updated_at == updated_at


def test_users_compare_by_entity_type_and_id() -> None:
    entity_id = uuid4()
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    first = User(
        entity_id, EmailAddress("first@example.com"), None, None, created_at, created_at
    )
    second = User(
        entity_id,
        EmailAddress("second@example.com"),
        None,
        None,
        created_at,
        created_at,
    )

    assert first == second
    assert hash(first) == hash(second)
