import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies.database import get_db
from app.main import create_app


class FakeSession:
    def __init__(self, error: SQLAlchemyError | None = None) -> None:
        self.error = error
        self.executed = False

    def execute(self, statement: object) -> None:
        self.executed = True
        assert str(statement) == str(text("SELECT 1"))
        if self.error:
            raise self.error


def make_app(session: FakeSession | None = None) -> FastAPI:
    application = create_app()
    if session is not None:
        application.dependency_overrides[get_db] = lambda: session
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


@pytest.mark.anyio
async def test_liveness_reports_service_available() -> None:
    response = await request_health("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"message": "OK", "data": {"status": "OK"}}


@pytest.mark.anyio
async def test_readiness_reports_database_available() -> None:
    session = FakeSession()
    response = await request_health("/api/v1/health/ready", session)

    assert response.status_code == 200
    assert response.json() == {
        "message": "OK",
        "data": {"status": "OK", "database": {"status": "OK", "message": None}},
    }
    assert session.executed


@pytest.mark.anyio
async def test_readiness_reports_database_unavailable() -> None:
    session = FakeSession(SQLAlchemyError("Database unavailable"))
    response = await request_health("/api/v1/health/ready", session)

    assert response.status_code == 503
    assert response.json() == {
        "message": "Service unavailable",
        "data": {
            "status": "UNAVAILABLE",
            "database": {
                "status": "UNAVAILABLE",
                "message": "Database connection failed",
            },
        },
    }
    assert session.executed
