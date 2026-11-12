import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.domain.development.entities.branch import Branch
from app.domain.development.enums import RepositoryType
from app.domain.projects import ProjectStatus, ProjectType
from app.infrastructure.persistence.models.development.repository import Repository
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.projects.project import Project
from app.infrastructure.persistence.repositories.development import (
    SqlAlchemyBranchRepository,
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
async def test_branch_repository_scopes_owner_and_switches_current_branch() -> None:
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
    main_id = uuid4()
    feature_id = uuid4()
    remote_id = uuid4()
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
                            display_name="Branch Owner",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                        User(
                            id=other_user_id,
                            email=f"{other_user_id}@example.test",
                            display_name="Other Branch Owner",
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
                            name="Branch Project",
                            slug=f"branch-{project_id}",
                            project_type=ProjectType.SOFTWARE,
                            status=ProjectStatus.ACTIVE,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Project(
                            id=other_project_id,
                            user_id=other_user_id,
                            name="Other Branch Project",
                            slug=f"other-branch-{other_project_id}",
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
                            name="branch-repository",
                            slug=f"branch-{repository_id}",
                            repository_type=RepositoryType.GIT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Repository(
                            id=other_repository_id,
                            project_id=other_project_id,
                            name="other-branch-repository",
                            slug=f"other-branch-{other_repository_id}",
                            repository_type=RepositoryType.GIT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                await session.flush()

                repository = SqlAlchemyBranchRepository(session)
                main = Branch(
                    entity_id=main_id,
                    repository_id=repository_id,
                    name="main",
                    commit_hash="a" * 40,
                    is_current=True,
                    last_updated_at=now,
                    last_synced_at=now,
                )
                feature = Branch(
                    entity_id=feature_id,
                    repository_id=repository_id,
                    name="feature/search",
                    commit_hash="b" * 40,
                    is_current=True,
                    last_updated_at=now,
                    last_synced_at=now,
                )
                remote_main = Branch(
                    entity_id=remote_id,
                    repository_id=repository_id,
                    name="main",
                    is_remote=True,
                )
                await repository.create(user_id, main)
                await session.flush()
                await repository.create(user_id, feature)
                await repository.create(user_id, remote_main)
                await session.flush()

                stored_main = await repository.get_by_id(user_id, main_id)
                stored_feature = await repository.get_by_id(user_id, feature_id)
                assert stored_main is not None and not stored_main.is_current
                assert stored_feature is not None and stored_feature.is_current
                assert await repository.get_by_id(other_user_id, feature_id) is None
                assert (
                    await repository.get_by_name(user_id, repository_id, "main", True)
                    == remote_main
                )
                assert [
                    branch.name
                    for branch in await repository.get_by_repository(user_id, repository_id)
                ] == ["feature/search", "main", "main"]

                updated_feature = Branch(
                    entity_id=feature_id,
                    repository_id=repository_id,
                    name="feature/index",
                    commit_hash="c" * 40,
                    is_current=True,
                    last_updated_at=datetime.now(UTC),
                    last_synced_at=now,
                )
                assert await repository.update(user_id, updated_feature)
                assert (
                    await repository.get_by_name(
                        user_id, repository_id, "feature/index", False
                    )
                    == updated_feature
                )
                assert await repository.delete(user_id, feature_id)
                assert await repository.get_by_id(user_id, feature_id) is None
            await transaction.rollback()
    finally:
        await engine.dispose()
