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
from app.domain.projects import (
    Environment as EnvironmentEntity,
)
from app.domain.projects import (
    EnvironmentName,
    EnvironmentType,
    ProjectStatus,
    ProjectType,
)
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.projects.environment import (
    Environment as EnvironmentModel,
)
from app.infrastructure.persistence.models.projects.project import Project
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyEnvironmentRepository,
)


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


@pytest.mark.anyio
async def test_create_persists_environment_through_orm_model() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    other_user_id = uuid4()
    project_id = uuid4()
    other_project_id = uuid4()
    environment_id = uuid4()
    now = datetime.now(UTC)
    environment = EnvironmentEntity(
        entity_id=environment_id,
        project_id=project_id,
        name=EnvironmentName("Integration"),
        environment_type=EnvironmentType.DEVELOPMENT,
        description="Repository integration test",
        configuration={"debug": True},
        created_at=now,
        updated_at=now,
    )
    identity = VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="environment-integration-test",
        expires_at=now + timedelta(hours=1),
        token_hash=TokenHash("f" * 64),
    )
    other_identity = VerifiedIdentity(
        user_id=other_user_id,
        email=EmailAddress(f"{other_user_id}@example.test"),
        auth_provider="environment-integration-test",
        expires_at=now + timedelta(hours=1),
        token_hash=TokenHash("e" * 64),
    )

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
                            display_name="Environment Repository Integration Test",
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
                            id=owner_project_id,
                            user_id=owner_id,
                            name="Environment Repository Integration Test",
                            slug=f"environment-repository-{owner_project_id}",
                            project_type=ProjectType.SOFTWARE,
                            status=ProjectStatus.ACTIVE,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        )
                        for owner_id, owner_project_id in (
                            (user_id, project_id),
                            (other_user_id, other_project_id),
                        )
                    ]
                )
                await session.flush()

                repository = SqlAlchemyEnvironmentRepository(session)
                assert await repository.create(identity, environment)
                assert not await repository.create(
                    identity,
                    EnvironmentEntity(
                        entity_id=uuid4(),
                        project_id=other_project_id,
                        name=EnvironmentName("Unauthorized"),
                        environment_type=EnvironmentType.DEVELOPMENT,
                        description=None,
                        configuration=None,
                        created_at=now,
                        updated_at=now,
                    ),
                )
                assert await repository.get_by_id(identity, environment_id) is not None
                assert await repository.get_by_id(other_identity, environment_id) is None
                assert await repository.get_active_by_project_id(identity, project_id)
                assert (
                    await repository.get_active_by_project_id(other_identity, project_id)
                    == []
                )

                updated_at = now + timedelta(seconds=1)
                updated = EnvironmentEntity(
                    entity_id=environment_id,
                    project_id=project_id,
                    name=EnvironmentName("Staging"),
                    environment_type=EnvironmentType.STAGING,
                    description="Updated environment",
                    configuration={"debug": False},
                    version=2,
                    created_at=now,
                    updated_at=updated_at,
                )
                assert await repository.update(identity, updated, expected_version=1)
                assert not await repository.update(
                    identity, environment, expected_version=1
                )
                assert not await repository.update(
                    other_identity, updated, expected_version=2
                )

                stored = await session.scalar(
                    select(EnvironmentModel).where(EnvironmentModel.id == environment_id)
                )
                assert stored is not None
                assert stored.id == environment_id
                assert stored.project_id == project_id
                assert stored.name == "Staging"
                assert stored.slug == "staging"
                assert stored.environment_type is EnvironmentType.STAGING
                assert stored.configuration == {"debug": False}
                assert stored.description == "Updated environment"
                assert stored.version == 2
                assert not await repository.delete(other_identity, environment_id)
                assert await repository.delete(identity, environment_id)
            await transaction.rollback()
    finally:
        await engine.dispose()
