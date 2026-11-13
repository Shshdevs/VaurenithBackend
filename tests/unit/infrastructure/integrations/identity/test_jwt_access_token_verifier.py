from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from pydantic import ValidationError
from tests.support_jwt import (
    TEST_AUDIENCE,
    TEST_ISSUER,
    TEST_PRIVATE_KEY_PEM,
    TEST_PUBLIC_KEY,
    make_access_token,
)

from app.core.config import Settings, get_settings
from app.infrastructure.integrations.identity import JwtAccessTokenVerifier


def make_verifier(**overrides: object) -> JwtAccessTokenVerifier:
    settings: dict[str, object] = {
        "public_key": TEST_PUBLIC_KEY,
        "issuer": TEST_ISSUER,
        "audience": TEST_AUDIENCE,
        "clock_skew_seconds": 2,
        "max_lifetime_seconds": 600,
    }
    settings.update(overrides)
    return JwtAccessTokenVerifier(**settings)


def encode(payload: dict[str, object], key: str | bytes, algorithm: str) -> str:
    return jwt.encode(payload, key, algorithm=algorithm, headers={"typ": "at+jwt"})


def test_verifies_valid_access_token() -> None:
    claims = make_verifier().verify(make_access_token())

    assert claims is not None
    assert claims.email == "user@example.test"
    assert claims.auth_provider == "local"


@pytest.mark.parametrize(
    "claim,value",
    [("iss", "https://wrong.test"), ("iss", None), ("aud", "other-service"), ("aud", None)],
)
def test_rejects_wrong_or_missing_issuer_and_audience(claim: str, value: object) -> None:
    token = make_access_token(
        {claim: value}, remove_claims=(claim,) if value is None else ()
    )

    assert make_verifier().verify(token) is None


@pytest.mark.parametrize("typ", ["JWT", "id+jwt", "refresh+jwt", None])
def test_rejects_wrong_or_missing_token_type(typ: str | None) -> None:
    token = make_access_token(headers={"typ": typ} if typ is not None else {})

    assert make_verifier().verify(token) is None


@pytest.mark.parametrize("algorithm", ["HS256", "HS384", "none"])
def test_rejects_non_rs256_algorithms(algorithm: str) -> None:
    claims = {
        "iss": TEST_ISSUER,
        "aud": TEST_AUDIENCE,
        "sub": str(uuid4()),
        "iat": datetime.now(UTC),
        "nbf": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=1),
        "jti": str(uuid4()),
        "email": "user@example.test",
        "auth_provider": "local",
    }
    key = "x" * 64 if algorithm.startswith("HS") else ""
    token = encode(claims, key, algorithm)

    assert make_verifier().verify(token) is None


def test_rejects_invalid_signature() -> None:
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_key = other_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )

    assert make_verifier().verify(make_access_token(key=private_key)) is None


@pytest.mark.parametrize(
    "claim,value",
    [
        ("aud", [TEST_AUDIENCE]),
        ("sub", 123),
        ("iat", True),
        ("nbf", "tomorrow"),
        ("exp", False),
        ("email", 123),
        ("auth_provider", []),
        ("jti", 456),
    ],
)
def test_rejects_invalid_claim_types(claim: str, value: object) -> None:
    assert make_verifier().verify(make_access_token({claim: value})) is None


@pytest.mark.parametrize(
    "claim",
    ["iss", "aud", "sub", "exp", "iat", "nbf", "jti", "email", "auth_provider"],
)
def test_rejects_missing_required_claims(claim: str) -> None:
    assert make_verifier().verify(make_access_token(remove_claims=(claim,))) is None


def test_rejects_expired_token_and_future_activation_times() -> None:
    now = datetime.now(UTC)
    expired = make_access_token({"exp": now - timedelta(minutes=1)})
    inactive = make_access_token({"nbf": now + timedelta(minutes=1)})
    issued_in_future = make_access_token({"iat": now + timedelta(minutes=1)})

    assert make_verifier().verify(expired) is None
    assert make_verifier().verify(inactive) is None
    assert make_verifier().verify(issued_in_future) is None


def test_rejects_lifetime_over_limit_and_invalid_jti() -> None:
    now = datetime.now(UTC)
    assert (
        make_verifier().verify(
            make_access_token({"iat": now, "nbf": now, "exp": now + timedelta(minutes=11)})
        )
        is None
    )
    assert make_verifier().verify(make_access_token({"jti": ""})) is None
    assert make_verifier().verify(make_access_token({"jti": "not-a-uuid"})) is None


def test_startup_fails_closed_when_jwt_configuration_is_missing(
    monkeypatch, tmp_path
) -> None:
    for name in (
        "AUTH_JWT_ISSUER",
        "AUTH_JWT_AUDIENCE",
        "AUTH_JWT_PUBLIC_KEY_PATH",
        "AUTH_JWT_CLOCK_SKEW_SECONDS",
        "AUTH_JWT_MAX_LIFETIME_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.chdir(tmp_path)
    from app.main import create_app

    get_settings.cache_clear()
    with pytest.raises(ValidationError):
        create_app()


def test_settings_reject_invalid_public_key(tmp_path) -> None:
    key_path = tmp_path / "jwt-public.pem"
    key_path.write_text("invalid", encoding="ascii")
    with pytest.raises(ValueError):
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://user:password@localhost/test",
            auth_jwt_issuer=TEST_ISSUER,
            auth_jwt_audience=TEST_AUDIENCE,
            auth_jwt_public_key_path=key_path,
            auth_jwt_clock_skew_seconds=2,
            auth_jwt_max_lifetime_seconds=600,
            cors_origins="",
            api_prefix="/api/v1",
            log_level="INFO",
        )


def test_settings_reject_missing_public_key_file(tmp_path) -> None:
    with pytest.raises(FileNotFoundError):
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://user:password@localhost/test",
            auth_jwt_issuer=TEST_ISSUER,
            auth_jwt_audience=TEST_AUDIENCE,
            auth_jwt_public_key_path=tmp_path / "missing.pem",
            auth_jwt_clock_skew_seconds=2,
            auth_jwt_max_lifetime_seconds=600,
            cors_origins="",
            api_prefix="/api/v1",
            log_level="INFO",
        )


def test_settings_reject_private_key_material(tmp_path) -> None:
    key_path = tmp_path / "jwt-public.pem"
    key_path.write_text(TEST_PRIVATE_KEY_PEM, encoding="ascii")

    with pytest.raises(ValueError, match="must not contain private key material"):
        Settings(
            _env_file=None,
            database_url="postgresql+psycopg://user:password@localhost/test",
            auth_jwt_issuer=TEST_ISSUER,
            auth_jwt_audience=TEST_AUDIENCE,
            auth_jwt_public_key_path=key_path,
            auth_jwt_clock_skew_seconds=2,
            auth_jwt_max_lifetime_seconds=600,
            cors_origins="",
            api_prefix="/api/v1",
            log_level="INFO",
        )
