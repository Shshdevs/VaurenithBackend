import os

import pytest
from dotenv import load_dotenv

load_dotenv(override=False)

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://vaurenith_admin:password@localhost:5432/vaurenith",
)
os.environ.setdefault("AUTH_JWT_SECRET", "test-secret-for-authentication-32chars")
os.environ.setdefault("CORS_ORIGINS", "")
os.environ.setdefault("API_PREFIX", "/api/v1")
os.environ.setdefault("LOG_LEVEL", "INFO")


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
