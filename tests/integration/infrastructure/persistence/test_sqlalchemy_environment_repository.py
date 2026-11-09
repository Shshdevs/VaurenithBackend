import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
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
    project_id = uuid4()
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

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            async with AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            ) as session:
                session.add(
                    User(
                        id=user_id,
                        email=f"{user_id}@example.test",
                        display_name="Environment Repository Integration Test",
                        auth_provider="integration-test",
                        created_at=now,
                        updated_at=now,
                    )
                )
                session.add(
                    Project(
                        id=project_id,
                        user_id=user_id,
                        name="Environment Repository Integration Test",
                        slug=f"environment-repository-{project_id}",
                        project_type=ProjectType.SOFTWARE,
                        status=ProjectStatus.ACTIVE,
                        version=1,
                        created_at=now,
                        updated_at=now,
                    )
                )
                await session.flush()

                await SqlAlchemyEnvironmentRepository(session).create(environment)

                stored = await session.scalar(
                    select(EnvironmentModel).where(EnvironmentModel.id == environment_id)
                )
                assert stored is not None
                assert stored.id == environment_id
                assert stored.project_id == project_id
                assert stored.name == "Integration"
                assert stored.slug == "integration"
                assert stored.environment_type is EnvironmentType.DEVELOPMENT
                assert stored.configuration == {"debug": True}
                assert stored.description == "Repository integration test"

            await transaction.rollback()
    finally:
        await engine.dispose()
