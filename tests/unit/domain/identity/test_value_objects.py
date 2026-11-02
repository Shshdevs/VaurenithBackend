import pytest

from app.domain.identity.exceptions import InvalidEmail, InvalidTokenHash
from app.domain.identity.value_objects.email import EmailAddress
from app.domain.identity.value_objects.token_hash import TokenHash


def test_email_address_trims_surrounding_whitespace() -> None:
    email = EmailAddress("  person@example.com  ")

    assert email.value == "person@example.com"


def test_email_addresses_compare_by_normalized_value() -> None:
    first = EmailAddress("person@example.com")
    second = EmailAddress(" person@example.com ")

    assert first == second
    assert hash(first) == hash(second)


@pytest.mark.parametrize(
    "value",
    ["", "not-an-email", "@example.com", "person@", "person@@example.com", "a" * 321],
)
def test_invalid_email_address_is_rejected(value: str) -> None:
    with pytest.raises(InvalidEmail):
        EmailAddress(value)


def test_token_hash_compares_by_value() -> None:
    first = TokenHash("sha256:token-digest")
    second = TokenHash("sha256:token-digest")

    assert first == second
    assert hash(first) == hash(second)


@pytest.mark.parametrize("value", ["", "contains whitespace", "x" * 513])
def test_invalid_token_hash_is_rejected(value: str) -> None:
    with pytest.raises(InvalidTokenHash):
        TokenHash(value)
