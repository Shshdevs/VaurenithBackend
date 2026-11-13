from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

TEST_ISSUER = "https://identity.test.vaurenith"
TEST_AUDIENCE = "vaurenith-backend-test"
TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
TEST_PRIVATE_KEY_PEM = TEST_PRIVATE_KEY.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
TEST_PUBLIC_KEY = (
    TEST_PRIVATE_KEY.public_key()
    .public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    .decode()
)


def make_access_token(
    claims: dict[str, object] | None = None,
    *,
    algorithm: str = "RS256",
    key: str | bytes | None = None,
    headers: dict[str, object] | None = None,
    remove_claims: tuple[str, ...] = (),
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, object] = {
        "iss": TEST_ISSUER,
        "aud": TEST_AUDIENCE,
        "sub": str(uuid4()),
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=10),
        "jti": str(uuid4()),
        "email": "user@example.test",
        "auth_provider": "local",
    }
    if claims is not None:
        payload.update(claims)
    for name in remove_claims:
        payload.pop(name, None)
    signing_key = key if key is not None else TEST_PRIVATE_KEY_PEM
    token_headers = {"typ": "at+jwt"} if headers is None else headers
    return jwt.encode(payload, signing_key, algorithm=algorithm, headers=token_headers)
