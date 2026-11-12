import asyncio
import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.application.identity import VerifiedIdentity
from app.core.config import get_settings
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure.enums import DeviceType
from app.domain.projects import ProjectDevice as ProjectDeviceEntity
from app.domain.projects import ProjectDeviceRole, ProjectStatus, ProjectType
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.infrastructure.device import Device
from app.infrastructure.persistence.models.projects import Project
from app.infrastructure.persistence.models.projects.project_device import ProjectDevice
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyProjectDeviceRepository,
)


def assert_test_database_is_separate(test_database_url: str) -> None:
    configured_database_url = get_settings().database_url
    test_database = make_url(test_database_url)
    configured_database = make_url(configured_database_url)
    if (
        test_database.drivername,
        test_database.host,
        test_database.port,
        test_database.database,
    ) == (
        configured_database.drivername,
        configured_database.host,
        configured_database.port,
        configured_database.database,
    ):
        pytest.fail("TEST_DATABASE_URL must point to a separate database")


@pytest.mark.anyio
async def test_project_device_concurrent_updates_accept_only_one_version() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL concurrency test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    project_id = uuid4()
    device_id = uuid4()
    project_device_id = uuid4()
    now = datetime.now(UTC)
    identity = VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="integration-test",
        expires_at=now.replace(year=now.year + 1),
        token_hash=TokenHash("c" * 64),
    )
    seeded = False
    try:
        async with AsyncSession(engine) as session, session.begin():
            session.add(
                User(
                    id=user_id,
                    email=f"{user_id}@example.test",
                    display_name="Project Device Concurrency Test",
                    auth_provider="integration-test",
                    created_at=now,
                    updated_at=now,
                )
            )
            session.add(
                Project(
                    id=project_id,
                    user_id=user_id,
                    name="Project Device Concurrency Test",
                    slug=f"project-device-concurrency-{project_id}",
                    project_type=ProjectType.SOFTWARE,
                    status=ProjectStatus.ACTIVE,
                    version=1,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.add(
                Device(
                    id=device_id,
                    user_id=user_id,
                    name="Project Device Concurrency Test",
                    slug=f"project-device-concurrency-{device_id}",
                    device_type=DeviceType.VPS,
                    version=1,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.add(
                ProjectDevice(
                    id=project_device_id,
                    project_id=project_id,
                    device_id=device_id,
                    role="deployer",
                    created_at=now,
                    version=1,
                )
            )
        seeded = True

        ready = asyncio.Barrier(2)

        async def update(role: str) -> int | None:
            updated = ProjectDeviceEntity(
                entity_id=project_device_id,
                project_id=project_id,
                device_id=device_id,
                role=ProjectDeviceRole(role),
                created_at=now,
                version=2,
            )
            async with AsyncSession(engine) as session, session.begin():
                await ready.wait()
                return await SqlAlchemyProjectDeviceRepository(session).update(
                    identity, updated, expected_version=1
                )

        results = await asyncio.gather(update("operator"), update("deployer"))
        assert sorted(results, key=lambda value: value is None) == [2, None]

        async with AsyncSession(engine) as session:
            stored = await session.get(ProjectDevice, project_device_id)
            assert stored is not None
            assert stored.version == 2

    finally:
        if seeded:
            async with AsyncSession(engine) as session, session.begin():
                await session.execute(
                    ProjectDevice.__table__.delete().where(
                        ProjectDevice.id == project_device_id
                    )
                )
                await session.execute(
                    Device.__table__.delete().where(Device.id == device_id)
                )
                await session.execute(
                    Project.__table__.delete().where(Project.id == project_id)
                )
                await session.execute(User.__table__.delete().where(User.id == user_id))
        await engine.dispose()


@pytest.mark.anyio
async def test_project_device_repository_crud_round_trip() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    other_user_id = uuid4()
    project_id = uuid4()
    other_project_id = uuid4()
    device_id = uuid4()
    other_device_id = uuid4()
    project_device_id = uuid4()
    now = datetime.now(UTC)
    identity = VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="integration-test",
        expires_at=now.replace(year=now.year + 1),
        token_hash=TokenHash("a" * 64),
    )
    project_device = ProjectDeviceEntity(
        entity_id=project_device_id,
        project_id=project_id,
        device_id=device_id,
        role=ProjectDeviceRole("deployer"),
        created_at=now,
    )

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            async with AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            ) as database_session:
                database_session.add_all(
                    [
                        User(
                            id=user_id,
                            email=f"{user_id}@example.test",
                            display_name="Project Device Integration Test",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                        User(
                            id=other_user_id,
                            email=f"{other_user_id}@example.test",
                            display_name="Other Project Device Owner",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                database_session.add(
                    Project(
                        id=project_id,
                        user_id=user_id,
                        name="Project Device Integration Test",
                        slug=f"project-device-{project_id}",
                        project_type=ProjectType.SOFTWARE,
                        status=ProjectStatus.ACTIVE,
                        version=1,
                        created_at=now,
                        updated_at=now,
                    )
                )
                database_session.add(
                    Device(
                        id=device_id,
                        user_id=user_id,
                        name="Project Device Integration Test",
                        slug=f"project-device-{device_id}",
                        device_type=DeviceType.VPS,
                        version=1,
                        created_at=now,
                        updated_at=now,
                    )
                )
                database_session.add(
                    Project(
                        id=other_project_id,
                        user_id=other_user_id,
                        name="Other Project Device Integration Test",
                        slug=f"other-project-device-{other_project_id}",
                        project_type=ProjectType.SOFTWARE,
                        status=ProjectStatus.ACTIVE,
                        version=1,
                        created_at=now,
                        updated_at=now,
                    )
                )
                database_session.add(
                    Device(
                        id=other_device_id,
                        user_id=other_user_id,
                        name="Other Project Device Integration Test",
                        slug=f"other-project-device-{other_device_id}",
                        device_type=DeviceType.VPS,
                        version=1,
                        created_at=now,
                        updated_at=now,
                    )
                )
                await database_session.flush()

                repository = SqlAlchemyProjectDeviceRepository(database_session)
                assert await repository.link(identity, project_device)
                foreign_device_link = ProjectDeviceEntity(
                    entity_id=uuid4(),
                    project_id=project_id,
                    device_id=other_device_id,
                    role=None,
                    created_at=now,
                )
                assert not await repository.link(identity, foreign_device_link)
                foreign_project_link = ProjectDeviceEntity(
                    entity_id=uuid4(),
                    project_id=other_project_id,
                    device_id=device_id,
                    role=None,
                    created_at=now,
                )
                assert not await repository.link(identity, foreign_project_link)

                stored = await repository.get_by_id(identity, project_device_id)
                assert stored is not None
                assert stored.project_id == project_id
                assert stored.device_id == device_id
                assert stored.role == "deployer"
                assert [
                    item.id
                    for item in await repository.get_by_project(identity, project_id)
                ] == [project_device_id]
                assert [
                    item.id for item in await repository.get_by_device(identity, device_id)
                ] == [project_device_id]
                assert (
                    await repository.get_by_id(
                        VerifiedIdentity(
                            user_id=other_user_id,
                            email=EmailAddress(f"{other_user_id}@example.test"),
                            auth_provider="integration-test",
                            expires_at=now.replace(year=now.year + 1),
                            token_hash=TokenHash("b" * 64),
                        ),
                        project_device_id,
                    )
                    is None
                )

                updated = ProjectDeviceEntity(
                    entity_id=project_device_id,
                    project_id=project_id,
                    device_id=device_id,
                    role=ProjectDeviceRole("operator"),
                    created_at=now,
                )
                unauthorized_update = ProjectDeviceEntity(
                    entity_id=project_device_id,
                    project_id=project_id,
                    device_id=other_device_id,
                    role=ProjectDeviceRole("operator"),
                    created_at=now,
                )
                assert (
                    await repository.update(
                        identity, unauthorized_update, expected_version=1
                    )
                    is None
                )
                assert await repository.update(identity, updated, expected_version=1) == 2
                assert (
                    await repository.update(
                        identity, unauthorized_update, expected_version=1
                    )
                    is None
                )
                stored_model = await database_session.scalar(
                    select(ProjectDevice).where(ProjectDevice.id == project_device_id)
                )
                assert stored_model is not None
                assert stored_model.role == "operator"
                assert stored_model.version == 2

                assert await repository.delete(identity, project_device_id)
                assert not await repository.delete(identity, project_device_id)
                assert await repository.get_by_id(identity, project_device_id) is None

            await transaction.rollback()
    finally:
        await engine.dispose()
