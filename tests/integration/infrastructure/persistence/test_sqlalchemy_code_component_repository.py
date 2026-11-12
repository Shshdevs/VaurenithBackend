import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.domain.development import CodeComponent, ComponentType, RepositoryType
from app.domain.projects import ProjectStatus, ProjectType
from app.infrastructure.persistence.models.development.repository import Repository
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.projects.project import Project
from app.infrastructure.persistence.repositories.development import (
    SqlAlchemyCodeComponentRepository,
)


def assert_test_database_is_separate(test_database_url: str) -> None:
    configured = make_url(get_settings().database_url)
    test = make_url(test_database_url)
    if (test.drivername, test.host, test.port, test.database) == (
        configured.drivername,
        configured.host,
        configured.port,
        configured.database,
    ):
        pytest.fail("TEST_DATABASE_URL must point to a separate database")


@pytest.mark.anyio
async def test_code_component_repository_scopes_ownership_and_versions() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    other_user_id = uuid4()
    project_id = uuid4()
    other_project_id = uuid4()
    repository_id = uuid4()
    other_repository_id = uuid4()
    root_id = uuid4()
    child_id = uuid4()
    now = datetime.now(UTC)

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
                            id=user_id,
                            email=f"{user_id}@example.test",
                            display_name="Code Component Owner",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                        User(
                            id=other_user_id,
                            email=f"{other_user_id}@example.test",
                            display_name="Other Code Component Owner",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                session.add_all(
                    [
                        Project(
                            id=project_id,
                            user_id=user_id,
                            name="Code Component Project",
                            slug=f"code-component-{project_id}",
                            project_type=ProjectType.SOFTWARE,
                            status=ProjectStatus.ACTIVE,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Project(
                            id=other_project_id,
                            user_id=other_user_id,
                            name="Other Code Component Project",
                            slug=f"other-code-component-{other_project_id}",
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
                        Repository(
                            id=repository_id,
                            project_id=project_id,
                            name="code-component-repository",
                            slug=f"code-component-{repository_id}",
                            repository_type=RepositoryType.GIT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Repository(
                            id=other_repository_id,
                            project_id=other_project_id,
                            name="other-code-component-repository",
                            slug=f"other-code-component-{other_repository_id}",
                            repository_type=RepositoryType.GIT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                await session.flush()

                repository = SqlAlchemyCodeComponentRepository(session)
                root = CodeComponent(
                    entity_id=root_id,
                    repository_id=repository_id,
                    name="src",
                    path="src",
                    component_type=ComponentType.DIRECTORY,
                    created_at=now,
                    updated_at=now,
                )
                child = CodeComponent(
                    entity_id=child_id,
                    repository_id=repository_id,
                    parent_id=root_id,
                    name="main.py",
                    path="src/main.py",
                    component_type=ComponentType.FILE,
                    language="python",
                    created_at=now,
                    updated_at=now,
                )
                await repository.create(user_id, root)
                await repository.create(user_id, child)
                await session.flush()

                assert await repository.get_by_id(other_user_id, root_id) is None
                assert (
                    await repository.get_by_repository(other_user_id, repository_id) == []
                )
                stored = await repository.get_by_id(user_id, child_id)
                assert stored is not None
                assert stored.parent_id == root_id
                assert stored.version == 1

                updated = CodeComponent(
                    entity_id=root_id,
                    repository_id=repository_id,
                    name="source",
                    path="source",
                    component_type=ComponentType.DIRECTORY,
                    created_at=now,
                    updated_at=datetime.now(UTC),
                    version=2,
                )
                assert await repository.update(user_id, updated, 1)
                assert not await repository.update(user_id, updated, 1)

                with pytest.raises(ValueError, match="referenced"):
                    await repository.delete(user_id, root_id, 2)
                assert await repository.delete(user_id, child_id, 1)
                assert await repository.delete(user_id, root_id, 2)
                assert await repository.get_by_id(user_id, root_id) is None
            await transaction.rollback()
    finally:
        await engine.dispose()
