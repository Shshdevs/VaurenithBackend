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
    Container,
    ContainerImage,
    ContainerName,
    ContainerRuntimeId,
    Device,
    DeviceName,
)
from app.domain.infrastructure.enums import (
    ContainerStatus,
    DeviceType,
    ResourceStatus,
    ServiceType,
)
from app.domain.projects.enums import EnvironmentType, ProjectStatus, ProjectType
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.infrastructure.container import (
    Container as ContainerModel,
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
    SqlAlchemyContainerRepository,
    SqlAlchemyDeviceRepository,
)


def make_identity(user_id) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="container-integration-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_container(
    container_id,
    device_id,
    project_id,
    environment_id,
    service_id,
    now: datetime,
    name: str = "api",
    version: int = 1,
) -> Container:
    return Container(
        entity_id=container_id,
        device_id=device_id,
        project_id=project_id,
        environment_id=environment_id,
        service_id=service_id,
        container_runtime_id=ContainerRuntimeId("docker:api-123"),
        name=ContainerName(name),
        image=ContainerImage("example/api:1.0"),
        status=ContainerStatus.RUNNING,
        ports={"8080/tcp": [8080]},
        created_at=now,
        updated_at=now,
        version=version,
    )


@pytest.mark.anyio
async def test_container_repository_enforces_ownership_associations_and_versions() -> None:
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
                            display_name="Container Integration Test",
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
                            name="Container Project",
                            slug=f"container-{project_id}",
                            project_type=ProjectType.SOFTWARE,
                            status=ProjectStatus.ACTIVE,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Project(
                            id=other_project_id,
                            user_id=other_user_id,
                            name="Other Container Project",
                            slug=f"other-container-{other_project_id}",
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
                        name=DeviceName("container-host"),
                        device_type=DeviceType.VPS,
                        created_at=now,
                        updated_at=now,
                    )
                )
                await device_repository.create(
                    Device(
                        entity_id=other_device_id,
                        user_id=other_user_id,
                        name=DeviceName("other-container-host"),
                        device_type=DeviceType.VPS,
                        created_at=now,
                        updated_at=now,
                    )
                )
                session.add_all(
                    [
                        ServiceModel(
                            id=service_id,
                            device_id=device_id,
                            project_id=project_id,
                            environment_id=environment_id,
                            name="api",
                            slug="api",
                            service_type=ServiceType.APPLICATION,
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
                            name="other-api",
                            slug="other-api",
                            service_type=ServiceType.APPLICATION,
                            status=ResourceStatus.RUNNING,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                await session.flush()

                repository = SqlAlchemyContainerRepository(session)
                container = make_container(
                    container_id,
                    device_id,
                    project_id,
                    environment_id,
                    service_id,
                    now,
                )
                assert await repository.create(identity, container)
                stored = await repository.get_by_id(identity, container_id)
                assert stored is not None
                assert stored.name == "api"
                assert stored.image == "example/api:1.0"
                assert stored.metadata is None
                assert await repository.get_by_id(other_identity, container_id) is None
                assert [item.id for item in await repository.get_by_user(identity)] == [
                    container_id
                ]
                assert await repository.get_by_user(other_identity) == []
                assert [
                    item.id for item in await repository.get_by_device(identity, device_id)
                ] == [container_id]
                assert [
                    item.id
                    for item in await repository.get_by_project(identity, project_id)
                ] == [container_id]
                assert [
                    item.id
                    for item in await repository.get_by_environment(
                        identity, environment_id
                    )
                ] == [container_id]
                assert [
                    item.id
                    for item in await repository.get_by_service(identity, service_id)
                ] == [container_id]
                assert await repository.get_by_project(other_identity, project_id) == []
                assert (
                    await repository.get_by_environment(other_identity, environment_id)
                    == []
                )
                assert await repository.get_by_service(other_identity, service_id) == []

                assert not await repository.create(
                    identity,
                    make_container(
                        uuid4(),
                        other_device_id,
                        project_id,
                        environment_id,
                        service_id,
                        now,
                    ),
                )
                assert not await repository.create(
                    identity,
                    make_container(
                        uuid4(),
                        device_id,
                        other_project_id,
                        other_environment_id,
                        other_service_id,
                        now,
                    ),
                )
                assert not await repository.create(
                    identity,
                    make_container(
                        uuid4(),
                        device_id,
                        project_id,
                        environment_id,
                        other_service_id,
                        now,
                    ),
                )

                updated_at = now + timedelta(seconds=1)
                updated = Container(
                    entity_id=container_id,
                    device_id=device_id,
                    project_id=project_id,
                    environment_id=environment_id,
                    service_id=service_id,
                    container_runtime_id=ContainerRuntimeId("docker:api-123"),
                    name=ContainerName("api-v2"),
                    image=ContainerImage("example/api:2.0"),
                    status=ContainerStatus.PAUSED,
                    ports={"8081/tcp": [8081]},
                    created_at=now,
                    updated_at=updated_at,
                    version=2,
                )
                assert await repository.update(identity, updated, expected_version=1)
                assert not await repository.update(identity, container, expected_version=1)
                assert not await repository.update(
                    other_identity, updated, expected_version=2
                )
                updated_model = await session.scalar(
                    select(ContainerModel).where(ContainerModel.id == container_id)
                )
                assert updated_model is not None
                assert updated_model.name == "api-v2"
                assert updated_model.slug == "api-v2"
                assert updated_model.version == 2
                assert updated_model.status is ContainerStatus.PAUSED

                assert await device_repository.delete(
                    identity, device_id, now + timedelta(seconds=2)
                )
                deleted_device = await session.scalar(
                    select(DeviceModel).where(DeviceModel.id == device_id)
                )
                other_device = await session.scalar(
                    select(DeviceModel).where(DeviceModel.id == other_device_id)
                )
                assert deleted_device is not None
                assert deleted_device.deleted_at is not None
                assert other_device is not None
                assert other_device.deleted_at is None
                assert await repository.get_by_user(identity) == []
                assert await repository.get_by_id(identity, container_id) is None
                assert await repository.get_by_device(identity, device_id) == []
                assert not await repository.delete(identity, container_id)
                assert not await repository.update(identity, updated, expected_version=2)

                assert not await repository.delete(other_identity, container_id)
            await transaction.rollback()
    finally:
        await engine.dispose()
