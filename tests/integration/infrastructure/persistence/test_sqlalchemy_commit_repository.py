import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.domain.development.entities.commit import Commit
from app.domain.development.enums import RepositoryType
from app.domain.projects import ProjectStatus, ProjectType
from app.infrastructure.persistence.models.development.repository import Repository
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.projects.project import Project
from app.infrastructure.persistence.repositories.development import (
    SqlAlchemyCommitRepository,
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
async def test_commit_repository_scopes_ownership_and_maps_cached_metadata() -> None:
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
    commit_id = uuid4()
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
                            display_name="Commit Owner",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                        User(
                            id=other_user_id,
                            email=f"{other_user_id}@example.test",
                            display_name="Other Commit Owner",
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
                            name="Commit Project",
                            slug=f"commit-{project_id}",
                            project_type=ProjectType.SOFTWARE,
                            status=ProjectStatus.ACTIVE,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Project(
                            id=other_project_id,
                            user_id=other_user_id,
                            name="Other Commit Project",
                            slug=f"other-commit-{other_project_id}",
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
                            name="commit-repository",
                            slug=f"commit-{repository_id}",
                            repository_type=RepositoryType.GIT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Repository(
                            id=other_repository_id,
                            project_id=other_project_id,
                            name="other-commit-repository",
                            slug=f"other-commit-{other_repository_id}",
                            repository_type=RepositoryType.GIT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                await session.flush()

                repository = SqlAlchemyCommitRepository(session)
                commit = Commit(
                    entity_id=commit_id,
                    repository_id=repository_id,
                    hash="A" * 40,
                    author_name="Ada Lovelace",
                    author_email="ada@example.test",
                    message="Initial commit",
                    committed_at=now,
                    changed_files=["src/main.py"],
                    cached_at=now,
                )
                await repository.create(user_id, commit)
                await session.flush()

                stored = await repository.get_by_id(user_id, commit_id)
                assert stored == commit
                assert stored is not None
                assert stored.hash == "a" * 40
                assert await repository.get_by_id(other_user_id, commit_id) is None
                assert (
                    await repository.get_by_repository(other_user_id, repository_id) == []
                )
                assert (
                    await repository.get_by_hash(user_id, repository_id, "a" * 40) == commit
                )
                assert await repository.get_by_repository(user_id, repository_id) == [
                    commit
                ]
            await transaction.rollback()
    finally:
        await engine.dispose()
