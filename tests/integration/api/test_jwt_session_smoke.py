from __future__ import annotations

import hashlib
import os
import sys
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import UUID, uuid4

import jwt
import psycopg
import pytest
from alembic import command
from alembic.config import Config
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from sqlalchemy.engine import make_url


def database_identity(url: str) -> tuple[str, str | None, int | None, str | None]:
    parsed = make_url(url)
    return parsed.drivername, parsed.host, parsed.port, parsed.database


def postgres_url(url: str) -> str:
    return make_url(url).set(drivername="postgresql").render_as_string(hide_password=False)


def encode_token(
    private_key: rsa.RSAPrivateKey,
    *,
    user_id: UUID,
    email: str,
    overrides: Mapping[str, object] | None = None,
    remove_claims: tuple[str, ...] = (),
    algorithm: str = "RS256",
    signing_key: str | rsa.RSAPrivateKey | None = None,
    token_type: str = "at+jwt",
) -> str:
    now = datetime.now(UTC)
    claims: dict[str, object] = {
        "iss": "https://identity.smoke.test",
        "aud": "vaurenith-backend-smoke-test",
        "sub": str(user_id),
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=2),
        "jti": str(uuid4()),
        "email": email,
        "auth_provider": "smoke-test",
    }
    claims.update(overrides or {})
    for claim in remove_claims:
        claims.pop(claim, None)
    key = signing_key if signing_key is not None else private_key
    return jwt.encode(claims, key, algorithm=algorithm, headers={"typ": token_type})


def database_counts(sync_database_url: str) -> tuple[int, int]:
    with psycopg.connect(sync_database_url) as connection:
        users_row = connection.execute("SELECT count(*) FROM identity.users").fetchone()
        sessions_row = connection.execute(
            "SELECT count(*) FROM identity.sessions"
        ).fetchone()
    if users_row is None or sessions_row is None:
        raise RuntimeError("Could not read test database counters")
    return users_row[0], sessions_row[0]


def run_smoke_test() -> None:
    project_root = Path(__file__).resolve().parents[3]
    source_path = str(project_root / "src")
    if source_path not in sys.path:
        sys.path.insert(0, source_path)
    file_settings = dotenv_values(project_root / ".env")
    test_database_url = os.environ.get("TEST_DATABASE_URL") or file_settings.get(
        "TEST_DATABASE_URL"
    )
    application_database_url = os.environ.get("DATABASE_URL") or file_settings.get(
        "DATABASE_URL"
    )
    if not test_database_url:
        raise RuntimeError("Set TEST_DATABASE_URL to a dedicated PostgreSQL test database")
    if application_database_url:
        test_identity = database_identity(test_database_url)
        application_identity = database_identity(application_database_url)
        if (
            test_identity == application_identity
            or test_identity[-1] == application_identity[-1]
        ):
            raise RuntimeError("TEST_DATABASE_URL must point to a separate database")

    os.environ["DATABASE_URL"] = test_database_url
    os.environ["AUTH_JWT_ISSUER"] = "https://identity.smoke.test"
    os.environ["AUTH_JWT_AUDIENCE"] = "vaurenith-backend-smoke-test"
    os.environ["AUTH_JWT_CLOCK_SKEW_SECONDS"] = "2"
    os.environ["AUTH_JWT_MAX_LIFETIME_SECONDS"] = "300"
    os.environ["CORS_ORIGINS"] = os.environ.get("CORS_ORIGINS") or ""
    os.environ["API_PREFIX"] = os.environ.get("API_PREFIX") or "/api/v1"
    os.environ["LOG_LEVEL"] = os.environ.get("LOG_LEVEL") or "INFO"

    with TemporaryDirectory(prefix="vaurenith-jwt-smoke-") as temporary_directory:
        temporary_path = Path(temporary_directory)
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_pem = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        public_key_path = temporary_path / "jwt-public.pem"
        public_key_path.write_bytes(public_pem)
        os.environ["AUTH_JWT_PUBLIC_KEY_PATH"] = str(public_key_path)
        wrong_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

        from app.core.config import get_settings

        get_settings.cache_clear()
        migration_config = Config(str(project_root / "alembic.ini"))
        command.upgrade(migration_config, "head")

        from app.main import create_app

        sync_database_url = postgres_url(test_database_url)
        before_counts = database_counts(sync_database_url)
        negative_scenarios = (
            (
                "wrong issuer",
                {"iss": "https://other-issuer.test"},
                (),
                "RS256",
                "at+jwt",
                None,
            ),
            ("wrong audience", {"aud": "another-service"}, (), "RS256", "at+jwt", None),
            (
                "audience array",
                {"aud": ["vaurenith-backend-smoke-test"]},
                (),
                "RS256",
                "at+jwt",
                None,
            ),
            ("ID token type", {}, (), "RS256", "id+jwt", None),
            ("refresh token type", {}, (), "RS256", "refresh+jwt", None),
            ("HS256", {}, (), "HS256", "at+jwt", "x" * 64),
            ("none algorithm", {}, (), "none", "at+jwt", ""),
            ("invalid signature", {}, (), "RS256", "at+jwt", wrong_private_key),
            (
                "expired",
                {"exp": datetime.now(UTC) - timedelta(minutes=1)},
                (),
                "RS256",
                "at+jwt",
                None,
            ),
            (
                "future nbf",
                {"nbf": datetime.now(UTC) + timedelta(minutes=1)},
                (),
                "RS256",
                "at+jwt",
                None,
            ),
            (
                "future iat",
                {"iat": datetime.now(UTC) + timedelta(minutes=1)},
                (),
                "RS256",
                "at+jwt",
                None,
            ),
            (
                "overlong lifetime",
                {
                    "iat": datetime.now(UTC),
                    "nbf": datetime.now(UTC),
                    "exp": datetime.now(UTC) + timedelta(minutes=6),
                },
                (),
                "RS256",
                "at+jwt",
                None,
            ),
            ("missing issuer", {}, ("iss",), "RS256", "at+jwt", None),
            ("missing audience", {}, ("aud",), "RS256", "at+jwt", None),
            ("missing subject", {}, ("sub",), "RS256", "at+jwt", None),
            ("missing expiry", {}, ("exp",), "RS256", "at+jwt", None),
            ("missing issued-at", {}, ("iat",), "RS256", "at+jwt", None),
            ("missing not-before", {}, ("nbf",), "RS256", "at+jwt", None),
            ("missing jti", {}, ("jti",), "RS256", "at+jwt", None),
            ("missing email", {}, ("email",), "RS256", "at+jwt", None),
            ("missing provider", {}, ("auth_provider",), "RS256", "at+jwt", None),
            ("invalid jti", {"jti": "not-a-uuid"}, (), "RS256", "at+jwt", None),
            ("invalid email type", {"email": 123}, (), "RS256", "at+jwt", None),
            ("invalid provider type", {"auth_provider": []}, (), "RS256", "at+jwt", None),
        )

        with TestClient(create_app()) as client:
            for (
                label,
                overrides,
                removed,
                algorithm,
                token_type,
                signer,
            ) in negative_scenarios:
                scenario_user_id = uuid4()
                scenario_email = f"jwt-smoke-{scenario_user_id}@example.test"
                token = encode_token(
                    private_key,
                    user_id=scenario_user_id,
                    email=scenario_email,
                    overrides=overrides,
                    remove_claims=removed,
                    algorithm=algorithm,
                    signing_key=signer,
                    token_type=token_type,
                )
                response = client.post(
                    "/api/v1/users/create",
                    headers={"Authorization": f"Bearer {token}"},
                    json={
                        "email": scenario_email,
                        "device_name": "JWT smoke",
                        "platform": "other",
                    },
                )
                if response.status_code != 401:
                    raise RuntimeError(
                        f"Negative scenario {label!r} returned {response.status_code}"
                    )
                if database_counts(sync_database_url) != before_counts:
                    raise RuntimeError(
                        f"Negative scenario {label!r} changed user or session rows"
                    )

            user_id = uuid4()
            email = f"jwt-session-smoke-{user_id}@example.test"
            token = encode_token(private_key, user_id=user_id, email=email)
            headers = {"Authorization": f"Bearer {token}"}
            creation_response = client.post(
                "/api/v1/users/create",
                headers=headers,
                json={
                    "email": email,
                    "display_name": "JWT Session Smoke Test",
                    "device_name": "JWT smoke device",
                    "platform": "other",
                },
            )
            if creation_response.status_code != 201:
                raise RuntimeError(f"Registration returned {creation_response.status_code}")

            current_user_response = client.get("/api/v1/users/me", headers=headers)
            if current_user_response.status_code != 200:
                raise RuntimeError(
                    f"GET /users/me returned {current_user_response.status_code}"
                )
            returned_user = current_user_response.json()["data"]
            if returned_user["id"] != str(user_id) or returned_user["email"] != email:
                raise RuntimeError("GET /users/me returned a different user")

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        with psycopg.connect(sync_database_url) as connection:
            session = connection.execute(
                """
                SELECT user_id, token_hash, expires_at, revoked_at
                FROM identity.sessions
                WHERE token_hash = %s
                """,
                (token_hash,),
            ).fetchone()
        if (
            session is None
            or str(session[0]) != str(user_id)
            or session[1] != token_hash
            or session[2] <= datetime.now(UTC)
            or session[3] is not None
        ):
            raise RuntimeError("The newly created JWT session is not active in PostgreSQL")

        print(
            f"Negative JWT scenarios rejected: {len(negative_scenarios)}; no rows created"
        )
        print(f"POST /users/create: {creation_response.status_code}")
        print(f"GET /users/me: {current_user_response.status_code}")
        print(f"Test user: {user_id} ({email})")
        print("PostgreSQL Session: active, user and SHA-256 token hash matched")


def main() -> int:
    try:
        run_smoke_test()
    except Exception as error:
        print(
            f"JWT session smoke test failed ({type(error).__name__}); "
            "check TEST_DATABASE_URL and PostgreSQL availability.",
            file=sys.stderr,
        )
        return 1
    return 0


def test_jwt_session_smoke() -> None:
    if os.environ.get("RUN_JWT_SESSION_SMOKE") != "1":
        pytest.skip("Set RUN_JWT_SESSION_SMOKE=1 to run the PostgreSQL JWT smoke test")
    run_smoke_test()


if __name__ == "__main__":
    raise SystemExit(main())
