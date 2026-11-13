from unittest.mock import Mock

from app.core.config import Settings
from app.infrastructure.persistence import database


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "database_url": "postgresql+psycopg://user:password@localhost/test",
        "auth_jwt_secret": "x" * 32,
        "cors_origins": "http://localhost",
        "api_prefix": "/api/v1",
        "log_level": "INFO",
    }
    values.update(overrides)
    return Settings(**values)


def test_engine_uses_configured_connection_and_pool_limits(monkeypatch) -> None:
    create_engine = Mock()
    monkeypatch.setattr(database, "create_async_engine", create_engine)

    database.create_database_engine(
        make_settings(
            database_connect_timeout=7,
            database_pool_size=3,
            database_max_overflow=2,
            database_pool_timeout=11,
        )
    )

    create_engine.assert_called_once_with(
        "postgresql+psycopg://user:password@localhost/test",
        connect_args={"connect_timeout": 7},
        pool_pre_ping=True,
        pool_size=3,
        max_overflow=2,
        pool_timeout=11,
    )


def test_engine_timeout_settings_have_bounded_defaults() -> None:
    settings = make_settings()

    assert settings.database_connect_timeout == 5
    assert settings.database_pool_timeout == 10
    assert settings.database_pool_size == 5
    assert settings.database_max_overflow == 5
