import os
import subprocess

from dotenv import dotenv_values
from sqlalchemy.engine import make_url


def _database_identity(
    database_url: str,
) -> tuple[str, int, str | None]:
    parsed_url = make_url(database_url)
    host = parsed_url.host
    if host is None or host.lower() in {"localhost", "127.0.0.1", "::1"}:
        host = "<loopback>"
    return (
        host,
        parsed_url.port or 5432,
        parsed_url.database,
    )


def main() -> int:
    dotenv = dotenv_values(".env")
    test_database_url = os.environ.get("TEST_DATABASE_URL") or dotenv.get(
        "TEST_DATABASE_URL"
    )
    database_url = os.environ.get("DATABASE_URL") or dotenv.get("DATABASE_URL")

    if not test_database_url:
        raise SystemExit("Set TEST_DATABASE_URL in the environment or .env.")
    if not database_url:
        raise SystemExit("Set DATABASE_URL in the environment or .env.")
    if _database_identity(test_database_url) == _database_identity(database_url):
        raise SystemExit(
            "Refusing to migrate the configured application database as a test database."
        )

    environment = os.environ.copy()
    environment["DATABASE_URL"] = test_database_url
    return subprocess.call(["alembic", "upgrade", "head"], env=environment)


if __name__ == "__main__":
    raise SystemExit(main())
