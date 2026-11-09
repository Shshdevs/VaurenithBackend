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
from app.domain.infrastructure import Device, DeviceName, Service, ServiceName
from app.domain.infrastructure.enums import DeviceType, ResourceStatus, ServiceType
from app.domain.infrastructure.value_objects import SystemIdentifier
from app.domain.projects.enums import EnvironmentType, ProjectStatus, ProjectType
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.infrastructure.service import (
    Service as ServiceModel,
)
from app.infrastructure.persistence.models.projects.environment import (
    Environment as EnvironmentModel,
)
from app.infrastructure.persistence.models.projects.project import Project
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDeviceRepository,
    SqlAlchemyServiceRepository,
)


def make_identity(user_id) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="service-integration-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("d" * 64),
    )


def make_service(
    service_id,
    device_id,
    now: datetime,
    project_id=None,
    environment_id=None,
    name: str = "api",
    version: int = 1,
) -> Service:
    return Service(
        entity_id=service_id,
        project_id=project_id,
        environment_id=environment_id,
        device_id=device_id,
        name=ServiceName(name),
        service_type=ServiceType.APPLICATION,
        description="Integration service",
        system_identifier=SystemIdentifier("systemd:api"),
        status=ResourceStatus.UNKNOWN,
        metadata={"port": 8080},
        version=version,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.anyio
async def test_service_repository_persists_and_enforces_owner_scope_and_versions() -> None:
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
    environment_id = uuid4()
    device_id = uuid4()
    service_id = uuid4()
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
                            display_name="Service Integration Test",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        )
                        for owner_id in (user_id, other_user_id)
                    ]
                )
                session.add(
                    Project(
                        id=project_id,
                        user_id=user_id,
                        name="Service Integration Project",
                        slug=f"service-{project_id}",
                        project_type=ProjectType.SOFTWARE,
                        status=ProjectStatus.ACTIVE,
                        version=1,
                        created_at=now,
                        updated_at=now,
                    )
                )
                session.add(
                    EnvironmentModel(
                        id=environment_id,
                        project_id=project_id,
                        name="Integration",
                        slug=f"integration-{environment_id}",
                        environment_type=EnvironmentType.DEVELOPMENT,
                        version=1,
                        created_at=now,
                        updated_at=now,
                    )
                )
                device = Device(
                    entity_id=device_id,
                    user_id=user_id,
                    name=DeviceName("service-host"),
                    device_type=DeviceType.VPS,
                    created_at=now,
                    updated_at=now,
                )
                await SqlAlchemyDeviceRepository(session).create(device)
                await session.flush()

                repository = SqlAlchemyServiceRepository(session)
                service = make_service(
                    service_id, device_id, now, project_id, environment_id
                )
                assert await repository.create(identity, service)
                stored = await repository.get_by_id(identity, service_id)
                assert stored is not None
                assert stored.name == "api"
                assert stored.slug == "api"
                assert stored.system_identifier == "systemd:api"
                assert stored.metadata == {"port": 8080}
                assert (await repository.get_by_id(other_identity, service_id)) is None
                assert [
                    item.id for item in await repository.get_by_device(identity, device_id)
                ] == [service_id]
                assert [
                    item.id
                    for item in await repository.get_by_project(identity, project_id)
                ] == [service_id]
                assert [
                    item.id
                    for item in await repository.get_by_environment(
                        identity, environment_id
                    )
                ] == [service_id]
                assert await repository.get_by_device(other_identity, device_id) == []

                updated = make_service(
                    service_id,
                    device_id,
                    now,
                    project_id,
                    environment_id,
                    name="api-v2",
                    version=2,
                )
                updated_at = now + timedelta(seconds=1)
                updated = Service(
                    entity_id=updated.id,
                    device_id=device_id,
                    project_id=project_id,
                    environment_id=environment_id,
                    name=ServiceName("api-v2"),
                    service_type=ServiceType.APPLICATION,
                    description="Integration service",
                    system_identifier=SystemIdentifier("systemd:api"),
                    status=ResourceStatus.RUNNING,
                    last_status_at=updated_at,
                    metadata={"port": 8081},
                    version=2,
                    created_at=now,
                    updated_at=updated_at,
                )
                assert await repository.update(identity, updated, expected_version=1)
                assert not await repository.update(identity, service, expected_version=1)
                assert not await repository.update(
                    other_identity, updated, expected_version=2
                )
                updated_model = await session.scalar(
                    select(ServiceModel).where(ServiceModel.id == service_id)
                )
                assert updated_model is not None
                assert updated_model.name == "api-v2"
                assert updated_model.version == 2
                assert updated_model.status is ResourceStatus.RUNNING

                assert not await repository.delete(other_identity, service_id)
                assert await repository.delete(identity, service_id)
                assert not await repository.delete(identity, service_id)

            await transaction.rollback()
    finally:
        await engine.dispose()
