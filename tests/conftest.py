import os
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from dotenv import load_dotenv

from tests.support_jwt import TEST_AUDIENCE, TEST_ISSUER, TEST_PUBLIC_KEY

load_dotenv(override=False)

os.environ["DATABASE_URL"] = os.environ.get("DATABASE_URL") or (
    "postgresql+psycopg://vaurenith_admin:password@localhost:5432/vaurenith"
)
os.environ["AUTH_JWT_ISSUER"] = TEST_ISSUER
os.environ["AUTH_JWT_AUDIENCE"] = TEST_AUDIENCE
_test_keys_dir = TemporaryDirectory()
_test_public_key_path = Path(_test_keys_dir.name) / "jwt-public.pem"
_test_public_key_path.write_text(TEST_PUBLIC_KEY, encoding="ascii")
os.environ["AUTH_JWT_PUBLIC_KEY_PATH"] = str(_test_public_key_path)
os.environ["AUTH_JWT_CLOCK_SKEW_SECONDS"] = "30"
os.environ["AUTH_JWT_MAX_LIFETIME_SECONDS"] = "3600"
os.environ["CORS_ORIGINS"] = os.environ.get("CORS_ORIGINS") or ""
os.environ["API_PREFIX"] = os.environ.get("API_PREFIX") or "/api/v1"
os.environ["LOG_LEVEL"] = os.environ.get("LOG_LEVEL") or "INFO"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
