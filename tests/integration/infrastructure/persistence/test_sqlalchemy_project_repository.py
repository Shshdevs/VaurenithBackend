import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.domain.projects import Project, ProjectName, ProjectStatus, ProjectType
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.projects import Project as ProjectModel
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyProjectRepository,
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
async def test_create_persists_project_and_custom_version_then_rolls_back() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    project_id = uuid4()
    now = datetime.now(UTC)
    project = Project(
        entity_id=project_id,
        user_id=user_id,
        name=ProjectName("Docker database integration project"),
        description="Repository integration test",
        project_type=ProjectType.SOFTWARE,
        status=ProjectStatus.ACTIVE,
        metadata={"integration": True},
        version=7,
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
            ) as database_session:
                database_session.add(
                    User(
                        id=user_id,
                        email=f"{user_id}@example.test",
                        display_name="Project Repository Integration Test",
                        auth_provider="integration-test",
                        created_at=now,
                        updated_at=now,
                    )
                )
                await database_session.flush()

                await SqlAlchemyProjectRepository(database_session).create(project)

                stored_project = await database_session.scalar(
                    select(ProjectModel).where(ProjectModel.id == project_id)
                )
                assert stored_project is not None
                assert stored_project.user_id == user_id
                assert stored_project.name == "Docker database integration project"
                assert stored_project.project_type is ProjectType.SOFTWARE
                assert stored_project.status is ProjectStatus.ACTIVE
                assert stored_project.metadata_ == {"integration": True}
                assert stored_project.version == 7
                assert stored_project.created_at == now
                assert stored_project.updated_at == now

            await transaction.rollback()
    finally:
        await engine.dispose()
