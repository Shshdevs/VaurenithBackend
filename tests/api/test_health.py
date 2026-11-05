from datetime import datetime, timedelta

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.bootstrap.dependencies import get_database_session
from app.main import create_app


class FakeSession:
    def __init__(self, error: SQLAlchemyError | None = None) -> None:
        self.error = error
        self.executed = False

    async def execute(self, statement: object) -> None:
        self.executed = True
        assert str(statement) == str(text("SELECT 1"))
        if self.error:
            raise self.error


def make_app(session: FakeSession | None = None) -> FastAPI:
    application = create_app()
    if session is not None:
        application.dependency_overrides[get_database_session] = lambda: session
    return application


async def request_health(
    path: str,
    session: FakeSession | None = None,
) -> httpx.Response:
    application = make_app(session)
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.get(path)


def assert_utc_timestamp(data: dict[str, object]) -> None:
    timestamp = data.get("timestamp")
    assert isinstance(timestamp, str)
    parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    assert parsed_timestamp.utcoffset() == timedelta(0)


@pytest.mark.anyio
async def test_liveness_reports_service_available() -> None:
    response = await request_health("/api/v1/health")

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Service is healthy"
    assert body["status"] == "200 OK"
    assert body["data"]["status"] == "OK"
    assert set(body["data"]) == {"status", "timestamp"}
    assert_utc_timestamp(body["data"])


@pytest.mark.anyio
async def test_readiness_reports_database_available() -> None:
    session = FakeSession()
    response = await request_health("/api/v1/health/ready", session)

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Service is ready"
    assert body["status"] == "200 OK"
    assert body["data"]["status"] == "OK"
    assert body["data"]["database"] == {"status": "OK", "message": "Database is ready"}
    assert set(body["data"]) == {"status", "timestamp", "database"}
    assert_utc_timestamp(body["data"])
    assert session.executed


@pytest.mark.anyio
async def test_readiness_reports_database_unavailable() -> None:
    session = FakeSession(SQLAlchemyError("Database unavailable"))
    response = await request_health("/api/v1/health/ready", session)

    assert response.status_code == 503
    body = response.json()
    assert body["message"] == "Service unavailable"
    assert body["status"] == "503 Service Unavailable"
    assert body["data"]["status"] == "UNAVAILABLE"
    assert body["data"]["database"] == {
        "status": "UNAVAILABLE",
        "message": "Database connection failed",
    }
    assert set(body["data"]) == {"status", "timestamp", "database"}
    assert_utc_timestamp(body["data"])
    assert session.executed
