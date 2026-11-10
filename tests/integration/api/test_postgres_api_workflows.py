import os
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

import httpx
import jwt
import pytest
from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.application.infrastructure.use_cases.device import CreateDevice
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.dependencies.infrastructure.device import get_create_device_dependency
from app.core.config import get_settings
from app.infrastructure.persistence.models.identity.session import Session
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.infrastructure.device import Device
from app.infrastructure.persistence.models.projects.environment import Environment
from app.infrastructure.persistence.models.projects.project import Project
from app.infrastructure.persistence.models.projects.project_device import ProjectDevice
from app.infrastructure.persistence.models.synchronization import (
    ChangeLog,
    ChangeLogRetention,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDeviceRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork
from app.main import create_app


def assert_test_database_is_separate(test_database_url: str) -> None:
    configured_url = make_url(get_settings().database_url)
    test_url = make_url(test_database_url)
    if (
        test_url.drivername,
        test_url.host,
        test_url.port,
        test_url.database,
    ) == (
        configured_url.drivername,
        configured_url.host,
        configured_url.port,
        configured_url.database,
    ):
        pytest.fail("TEST_DATABASE_URL must point to a separate database")


def make_access_token(user_id) -> tuple[str, str]:
    email = f"{user_id}@example.test"
    token = jwt.encode(
        {
            "sub": str(user_id),
            "exp": datetime.now(UTC) + timedelta(hours=1),
            "email": email,
            "auth_provider": "postgres-api-integration-test",
        },
        get_settings().auth_jwt_secret.get_secret_value(),
        algorithm="HS256",
    )
    return token, email


class FailingRecorder:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, *_args, **_kwargs) -> None:
        await self._session.flush()
        raise RuntimeError("Change log write failed")


@pytest.mark.anyio
async def test_device_api_uses_postgres_change_log_and_enforces_owner_scope() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL API integration tests")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    owner_id, other_owner_id = uuid4(), uuid4()
    owner_token, owner_email = make_access_token(owner_id)
    other_token, other_email = make_access_token(other_owner_id)
    now = datetime.now(UTC)
    created_device_id = None
    created_project_id = None
    created_environment_id = None
    created_project_device_id = None
    application = create_app()

    async def override_database_session():
        async with (
            AsyncSession(engine, expire_on_commit=False) as session,
            session.begin(),
        ):
            yield session

    application.dependency_overrides[get_database_session] = override_database_session

    try:
        async with AsyncSession(engine) as session, session.begin():
            session.add_all(
                [
                    User(
                        id=owner_id,
                        email=owner_email,
                        auth_provider="postgres-api-integration-test",
                        created_at=now,
                        updated_at=now,
                    ),
                    User(
                        id=other_owner_id,
                        email=other_email,
                        auth_provider="postgres-api-integration-test",
                        created_at=now,
                        updated_at=now,
                    ),
                    Session(
                        user_id=owner_id,
                        token_hash=sha256(owner_token.encode()).hexdigest(),
                        expires_at=now + timedelta(hours=1),
                        created_at=now,
                    ),
                    Session(
                        user_id=other_owner_id,
                        token_hash=sha256(other_token.encode()).hexdigest(),
                        expires_at=now + timedelta(hours=1),
                        created_at=now,
                    ),
                ]
            )

        transport = httpx.ASGITransport(
            app=application,
            raise_app_exceptions=False,
        )
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            owner_headers = {"Authorization": f"Bearer {owner_token}"}
            other_headers = {"Authorization": f"Bearer {other_token}"}
            create_response = await client.post(
                "/api/v1/devices",
                headers=owner_headers,
                json={"name": "api-worker", "device_type": "vps"},
            )
            assert create_response.status_code == 201
            created_device_id = create_response.json()["data"]["id"]

            owner_list = await client.get("/api/v1/devices", headers=owner_headers)
            other_list = await client.get("/api/v1/devices", headers=other_headers)
            other_detail = await client.get(
                f"/api/v1/devices/{created_device_id}", headers=other_headers
            )
            other_update = await client.put(
                f"/api/v1/devices/{created_device_id}",
                headers=other_headers,
                json={"name": "foreign-update", "device_type": "vps", "version": 1},
            )
            other_delete = await client.delete(
                f"/api/v1/devices/{created_device_id}", headers=other_headers
            )
            assert [device["id"] for device in owner_list.json()["data"]] == [
                created_device_id
            ]
            assert other_list.json()["data"] == []
            assert other_detail.status_code == 404
            assert other_update.status_code == 404
            assert other_delete.status_code == 404

            project_response = await client.post(
                "/api/v1/projects",
                headers=owner_headers,
                json={"name": "api-project", "project_type": "software"},
            )
            assert project_response.status_code == 201
            created_project_id = project_response.json()["data"]["id"]
            assert (
                await client.get(
                    f"/api/v1/projects/{created_project_id}", headers=other_headers
                )
            ).status_code == 404

            environment_response = await client.post(
                f"/api/v1/projects/{created_project_id}/environments",
                headers=owner_headers,
                json={"name": "integration", "environment_type": "testing"},
            )
            assert environment_response.status_code == 201
            created_environment_id = environment_response.json()["data"]["id"]
            assert (
                await client.get(
                    f"/api/v1/projects/{created_project_id}/environments",
                    headers=other_headers,
                )
            ).status_code == 404

            link_response = await client.post(
                "/api/v1/project_devices",
                headers=owner_headers,
                json={
                    "project_id": created_project_id,
                    "device_id": created_device_id,
                    "role": "operator",
                },
            )
            assert link_response.status_code == 201
            created_project_device_id = link_response.json()["data"]["id"]
            assert (
                await client.get(
                    f"/api/v1/project_devices/{created_project_device_id}",
                    headers=other_headers,
                )
            ).status_code == 404

            update_response = await client.put(
                f"/api/v1/devices/{created_device_id}",
                headers=owner_headers,
                json={"name": "api-worker-v2", "device_type": "vps", "version": 1},
            )
            assert update_response.status_code == 200
            assert update_response.json()["data"]["version"] == 2

            delete_response = await client.delete(
                f"/api/v1/devices/{created_device_id}", headers=owner_headers
            )
            assert delete_response.status_code == 200

            owner_changes = await client.get("/api/v1/change-logs", headers=owner_headers)
            other_changes = await client.get("/api/v1/change-logs", headers=other_headers)
            assert [
                (change["entity_type"], change["entity_id"], change["operation"])
                for change in owner_changes.json()["data"]
            ] == [
                ("device", created_device_id, "insert"),
                ("project", created_project_id, "insert"),
                ("environment", created_environment_id, "insert"),
                ("project_device", created_project_device_id, "insert"),
                ("device", created_device_id, "update"),
                ("device", created_device_id, "delete"),
            ]
            assert other_changes.json()["data"] == []

            async with AsyncSession(engine) as session, session.begin():
                session.add(
                    ChangeLogRetention(
                        user_id=owner_id,
                        expired_through_sequence=owner_changes.json()["data"][0][
                            "sequence"
                        ],
                    )
                )
            expired_cursor_response = await client.get(
                "/api/v1/change-logs?after_sequence=0",
                headers=owner_headers,
            )
            assert expired_cursor_response.status_code == 410
            assert expired_cursor_response.json()["data"]["resync_required"] is True
            assert expired_cursor_response.json()["data"]["restart_sequence"] == max(
                change["sequence"] for change in owner_changes.json()["data"]
            )

            async def provide_failing_create_device(
                session: AsyncSession = Depends(get_database_session, scope="function"),
            ) -> CreateDevice:
                return CreateDevice(
                    SqlAlchemyDeviceRepository(session),
                    FailingRecorder(session),
                    SqlAlchemyUnitOfWork(session),
                )

            application.dependency_overrides[get_create_device_dependency] = (
                provide_failing_create_device
            )
            failed_response = await client.post(
                "/api/v1/devices",
                headers=owner_headers,
                json={"name": "must-rollback", "device_type": "vps"},
            )
            assert failed_response.status_code == 500
            application.dependency_overrides.pop(get_create_device_dependency)

            logout_response = await client.post(
                "/api/v1/users/logout",
                headers=owner_headers,
            )
            assert logout_response.status_code == 200
            async with AsyncSession(engine) as session:
                revoked_at = await session.scalar(
                    select(Session.revoked_at).where(
                        Session.token_hash == sha256(owner_token.encode()).hexdigest()
                    )
                )
            assert revoked_at is not None
            assert (
                await client.get("/api/v1/devices", headers=owner_headers)
            ).status_code == 401
            assert (
                await client.post("/api/v1/users/logout", headers=owner_headers)
            ).status_code == 401

        async with AsyncSession(engine) as session:
            assert (
                await session.scalar(
                    select(Device.id).where(
                        Device.user_id == owner_id,
                        Device.name == "must-rollback",
                    )
                )
                is None
            )
            assert (
                await session.scalar(
                    select(ChangeLog.id).where(
                        ChangeLog.user_id == owner_id,
                        ChangeLog.payload["name"].astext == "must-rollback",
                    )
                )
                is None
            )

    finally:
        application.dependency_overrides.clear()
        async with engine.begin() as connection:
            await connection.execute(delete(ChangeLog).where(ChangeLog.user_id == owner_id))
            if created_project_device_id is not None:
                await connection.execute(
                    delete(ProjectDevice).where(
                        ProjectDevice.id == created_project_device_id
                    )
                )
            if created_environment_id is not None:
                await connection.execute(
                    delete(Environment).where(Environment.id == created_environment_id)
                )
            if created_project_id is not None:
                await connection.execute(
                    delete(Project).where(Project.id == created_project_id)
                )
            if created_device_id is not None:
                await connection.execute(delete(Device).where(Device.user_id == owner_id))
            await connection.execute(
                delete(Session).where(Session.user_id.in_([owner_id, other_owner_id]))
            )
            await connection.execute(
                delete(User).where(User.id.in_([owner_id, other_owner_id]))
            )
        await engine.dispose()
