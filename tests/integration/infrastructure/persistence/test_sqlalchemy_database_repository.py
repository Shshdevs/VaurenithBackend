import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.application.identity import VerifiedIdentity
from app.core.config import get_settings
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import (
    Database,
    DatabaseEndpoint,
    DatabaseResourceName,
    Device,
    DeviceName,
)
from app.domain.infrastructure.enums import (
    ContainerStatus,
    DbmsType,
    DeviceType,
    ResourceStatus,
    ServiceType,
)
from app.domain.projects.enums import EnvironmentType, ProjectStatus, ProjectType
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.infrastructure.container import (
    Container as ContainerModel,
)
from app.infrastructure.persistence.models.infrastructure.database import (
    Database as DatabaseModel,
)
from app.infrastructure.persistence.models.infrastructure.device import (
    Device as DeviceModel,
)
from app.infrastructure.persistence.models.infrastructure.service import (
    Service as ServiceModel,
)
from app.infrastructure.persistence.models.projects.environment import (
    Environment as EnvironmentModel,
)
from app.infrastructure.persistence.models.projects.project import Project
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDatabaseRepository,
    SqlAlchemyDeviceRepository,
)


def make_identity(user_id) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="database-integration-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )


def make_database(
    database_id,
    device_id,
    project_id,
    environment_id,
    container_id,
    service_id,
    now: datetime,
    name: str = "primary",
    version: int = 1,
) -> Database:
    return Database(
        entity_id=database_id,
        device_id=device_id,
        project_id=project_id,
        environment_id=environment_id,
        container_id=container_id,
        service_id=service_id,
        name=DatabaseResourceName(name),
        dbms_type=DbmsType.POSTGRESQL,
        endpoint=DatabaseEndpoint("database.internal", 5432),
        database_name=None,
        status=ResourceStatus.RUNNING,
        created_at=now,
        updated_at=now,
        version=version,
    )


@pytest.mark.anyio
async def test_database_repository_enforces_owner_associations_and_versions() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    configured_url = make_url(get_settings().database_url)
    test_url = make_url(test_database_url)
    if (test_url.drivername, test_url.host, test_url.port, test_url.database) == (
        configured_url.drivername,
        configured_url.host,
        configured_url.port,
        configured_url.database,
    ):
        pytest.fail("TEST_DATABASE_URL must point to a separate database")

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    other_user_id = uuid4()
    project_id = uuid4()
    other_project_id = uuid4()
    environment_id = uuid4()
    other_environment_id = uuid4()
    device_id = uuid4()
    other_device_id = uuid4()
    service_id = uuid4()
    other_service_id = uuid4()
    container_id = uuid4()
    other_container_id = uuid4()
    database_id = uuid4()
    retained_database_id = uuid4()
    now = datetime.now(UTC)
    identity = make_identity(user_id)
    other_identity = make_identity(other_user_id)

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            async with AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            ) as session:
                session.add_all(
                    [
                        User(
                            id=owner_id,
                            email=f"{owner_id}@example.test",
                            display_name="Database Integration Test",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        )
                        for owner_id in (user_id, other_user_id)
                    ]
                )
                session.add_all(
                    [
                        Project(
                            id=project_id,
                            user_id=user_id,
                            name="Database Project",
                            slug=f"database-{project_id}",
                            project_type=ProjectType.SOFTWARE,
                            status=ProjectStatus.ACTIVE,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Project(
                            id=other_project_id,
                            user_id=other_user_id,
                            name="Other Database Project",
                            slug=f"other-database-{other_project_id}",
                            project_type=ProjectType.SOFTWARE,
                            status=ProjectStatus.ACTIVE,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                session.add_all(
                    [
                        EnvironmentModel(
                            id=environment_id,
                            project_id=project_id,
                            name="Development",
                            slug=f"development-{environment_id}",
                            environment_type=EnvironmentType.DEVELOPMENT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        EnvironmentModel(
                            id=other_environment_id,
                            project_id=other_project_id,
                            name="Other Development",
                            slug=f"other-development-{other_environment_id}",
                            environment_type=EnvironmentType.DEVELOPMENT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                await session.flush()

                device_repository = SqlAlchemyDeviceRepository(session)
                await device_repository.create(
                    Device(
                        entity_id=device_id,
                        user_id=user_id,
                        name=DeviceName("database-host"),
                        device_type=DeviceType.VPS,
                        created_at=now,
                        updated_at=now,
                    )
                )
                await device_repository.create(
                    Device(
                        entity_id=other_device_id,
                        user_id=other_user_id,
                        name=DeviceName("other-database-host"),
                        device_type=DeviceType.VPS,
                        created_at=now,
                        updated_at=now,
                    )
                )
                await session.flush()

                session.add_all(
                    [
                        ServiceModel(
                            id=service_id,
                            device_id=device_id,
                            project_id=project_id,
                            environment_id=environment_id,
                            name="postgres-service",
                            slug="postgres-service",
                            service_type=ServiceType.DATABASE,
                            status=ResourceStatus.RUNNING,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        ServiceModel(
                            id=other_service_id,
                            device_id=other_device_id,
                            project_id=other_project_id,
                            environment_id=other_environment_id,
                            name="other-postgres-service",
                            slug="other-postgres-service",
                            service_type=ServiceType.DATABASE,
                            status=ResourceStatus.RUNNING,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                session.add_all(
                    [
                        ContainerModel(
                            id=container_id,
                            device_id=device_id,
                            project_id=project_id,
                            environment_id=environment_id,
                            service_id=service_id,
                            container_runtime_id="docker:postgres-123",
                            name="postgres",
                            slug="postgres",
                            status=ContainerStatus.RUNNING,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        ContainerModel(
                            id=other_container_id,
                            device_id=other_device_id,
                            project_id=other_project_id,
                            environment_id=other_environment_id,
                            service_id=other_service_id,
                            container_runtime_id="docker:other-postgres-123",
                            name="other-postgres",
                            slug="other-postgres",
                            status=ContainerStatus.RUNNING,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                await session.flush()

                database_repository = SqlAlchemyDatabaseRepository(session)
                database = make_database(
                    database_id,
                    device_id,
                    project_id,
                    environment_id,
                    container_id,
                    service_id,
                    now,
                )
                assert await database_repository.create(identity, database)
                stored = await database_repository.get_by_id(identity, database_id)
                assert stored is not None
                assert stored.name == "primary"
                assert stored.host == "database.internal"
                assert stored.port == 5432
                assert (
                    await database_repository.get_by_id(other_identity, database_id) is None
                )
                user_databases = await database_repository.get_by_user(identity)
                assert [item.id for item in user_databases] == [database_id]
                assert await database_repository.get_by_user(other_identity) == []
                assert [
                    item.id
                    for item in await database_repository.get_by_device(identity, device_id)
                ] == [database_id]
                assert [
                    item.id
                    for item in await database_repository.get_by_project(
                        identity, project_id
                    )
                ] == [database_id]
                assert [
                    item.id
                    for item in await database_repository.get_by_environment(
                        identity, environment_id
                    )
                ] == [database_id]
                assert [
                    item.id
                    for item in await database_repository.get_by_container(
                        identity, container_id
                    )
                ] == [database_id]
                assert [
                    item.id
                    for item in await database_repository.get_by_service(
                        identity, service_id
                    )
                ] == [database_id]
                assert (
                    await database_repository.get_by_container(other_identity, container_id)
                    == []
                )
                assert (
                    await database_repository.get_by_service(other_identity, service_id)
                    == []
                )

                invalid_associations = (
                    (
                        other_device_id,
                        project_id,
                        environment_id,
                        container_id,
                        service_id,
                    ),
                    (
                        device_id,
                        other_project_id,
                        other_environment_id,
                        other_container_id,
                        other_service_id,
                    ),
                    (
                        device_id,
                        project_id,
                        environment_id,
                        other_container_id,
                        service_id,
                    ),
                    (
                        device_id,
                        project_id,
                        environment_id,
                        container_id,
                        other_service_id,
                    ),
                )
                for (
                    invalid_device,
                    invalid_project,
                    invalid_environment,
                    invalid_container,
                    invalid_service,
                ) in invalid_associations:
                    invalid = make_database(
                        uuid4(),
                        invalid_device,
                        invalid_project,
                        invalid_environment,
                        invalid_container,
                        invalid_service,
                        now,
                    )
                    assert not await database_repository.create(identity, invalid)

                updated_at = now + timedelta(seconds=1)
                updated = Database(
                    entity_id=database_id,
                    device_id=device_id,
                    project_id=project_id,
                    environment_id=environment_id,
                    container_id=container_id,
                    service_id=service_id,
                    name=DatabaseResourceName("primary-v2"),
                    dbms_type=DbmsType.POSTGRESQL,
                    endpoint=DatabaseEndpoint("database.internal", 5433),
                    status=ResourceStatus.PAUSED,
                    created_at=now,
                    updated_at=updated_at,
                    version=2,
                )
                assert await database_repository.update(
                    identity, updated, expected_version=1
                )
                assert not await database_repository.update(
                    identity, database, expected_version=1
                )
                assert not await database_repository.update(
                    other_identity, updated, expected_version=2
                )
                updated_model = await session.scalar(
                    select(DatabaseModel).where(DatabaseModel.id == database_id)
                )
                assert updated_model is not None
                assert updated_model.name == "primary-v2"
                assert updated_model.version == 2
                assert updated_model.port == 5433
                assert updated_model.status is ResourceStatus.PAUSED

                assert await database_repository.delete(identity, database_id)
                assert not await database_repository.delete(identity, database_id)

                retained = make_database(
                    retained_database_id,
                    device_id,
                    project_id,
                    environment_id,
                    container_id,
                    service_id,
                    now,
                    name="retained",
                )
                assert await database_repository.create(identity, retained)
                assert await device_repository.delete(
                    identity, device_id, now + timedelta(seconds=2)
                )
                deleted_device = await session.scalar(
                    select(DeviceModel).where(DeviceModel.id == device_id)
                )
                other_device = await session.scalar(
                    select(DeviceModel).where(DeviceModel.id == other_device_id)
                )
                assert deleted_device is not None and deleted_device.deleted_at is not None
                assert other_device is not None and other_device.deleted_at is None
                assert await database_repository.get_by_user(identity) == []
                assert (
                    await database_repository.get_by_id(identity, retained_database_id)
                    is None
                )
                assert not await database_repository.delete(identity, retained_database_id)
            await transaction.rollback()
    finally:
        await engine.dispose()
