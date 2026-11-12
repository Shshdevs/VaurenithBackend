import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.domain.common.enums import RelationOrigin
from app.domain.development.entities.dependency import Dependency
from app.domain.development.enums import ComponentType, DependencyType, RepositoryType
from app.domain.projects import ProjectStatus, ProjectType
from app.infrastructure.persistence.models.development.code_component import (
    CodeComponent as CodeComponentModel,
)
from app.infrastructure.persistence.models.development.dependency import (
    Dependency as DependencyModel,
)
from app.infrastructure.persistence.models.development.repository import Repository
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.projects.project import Project
from app.infrastructure.persistence.repositories.development import (
    SqlAlchemyDependencyRepository,
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
async def test_dependency_repository_scopes_and_updates_graph_edges() -> None:
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
    foreign_repository_id = uuid4()
    source_id = uuid4()
    target_id = uuid4()
    foreign_component_id = uuid4()
    dependency_id = uuid4()
    foreign_dependency_id = uuid4()
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
                            display_name="Dependency Owner",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                        User(
                            id=other_user_id,
                            email=f"{other_user_id}@example.test",
                            display_name="Other Dependency Owner",
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
                            name="Dependency Project",
                            slug=f"dependency-{project_id}",
                            project_type=ProjectType.SOFTWARE,
                            status=ProjectStatus.ACTIVE,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Project(
                            id=other_project_id,
                            user_id=other_user_id,
                            name="Other Dependency Project",
                            slug=f"other-dependency-{other_project_id}",
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
                            name="dependency-source-repository",
                            slug=f"dependency-source-{repository_id}",
                            repository_type=RepositoryType.GIT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Repository(
                            id=other_repository_id,
                            project_id=project_id,
                            name="dependency-target-repository",
                            slug=f"dependency-target-{other_repository_id}",
                            repository_type=RepositoryType.GIT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                        Repository(
                            id=foreign_repository_id,
                            project_id=other_project_id,
                            name="foreign-dependency-repository",
                            slug=f"foreign-dependency-{foreign_repository_id}",
                            repository_type=RepositoryType.GIT,
                            version=1,
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                session.add_all(
                    [
                        CodeComponentModel(
                            id=source_id,
                            repository_id=repository_id,
                            name="source.py",
                            path="src/source.py",
                            component_type=ComponentType.FILE,
                            created_at=now,
                            updated_at=now,
                            version=1,
                        ),
                        CodeComponentModel(
                            id=target_id,
                            repository_id=other_repository_id,
                            name="target.py",
                            path="src/target.py",
                            component_type=ComponentType.FILE,
                            created_at=now,
                            updated_at=now,
                            version=1,
                        ),
                        CodeComponentModel(
                            id=foreign_component_id,
                            repository_id=foreign_repository_id,
                            name="foreign.py",
                            path="src/foreign.py",
                            component_type=ComponentType.FILE,
                            created_at=now,
                            updated_at=now,
                            version=1,
                        ),
                    ]
                )
                await session.flush()

                repository = SqlAlchemyDependencyRepository(session)
                dependency = Dependency(
                    entity_id=dependency_id,
                    source_component_id=source_id,
                    target_component_id=target_id,
                    dependency_type=DependencyType.IMPORT,
                    source_type=RelationOrigin.AUTOMATIC,
                    confidence=Decimal("0.8750"),
                    analysis_version="1.0",
                    analyzed_at=now,
                    metadata={"module": "target"},
                )
                await repository.create(user_id, dependency)
                await session.flush()

                session.add(
                    DependencyModel(
                        id=foreign_dependency_id,
                        source_component_id=source_id,
                        target_component_id=foreign_component_id,
                        dependency_type=DependencyType.CALL,
                        is_directed=True,
                        source_type=RelationOrigin.IMPORTED,
                    )
                )
                await session.flush()

                assert await repository.get_by_id(user_id, dependency_id) == dependency
                assert await repository.get_by_id(other_user_id, dependency_id) is None
                assert await repository.get_by_id(user_id, foreign_dependency_id) is None
                assert (
                    await repository.get_by_id(other_user_id, foreign_dependency_id) is None
                )
                assert await repository.get_by_component(user_id, source_id) == [dependency]
                assert await repository.get_by_component(user_id, target_id) == [dependency]
                assert await repository.get_by_repository(user_id, repository_id) == [
                    dependency
                ]
                assert await repository.get_by_repository(user_id, other_repository_id) == [
                    dependency
                ]
                assert (
                    await repository.get_by_key(
                        user_id, source_id, target_id, DependencyType.IMPORT
                    )
                    == dependency
                )

                with pytest.raises(ValueError, match="Code component"):
                    await repository.create(
                        user_id,
                        Dependency(
                            entity_id=uuid4(),
                            source_component_id=source_id,
                            target_component_id=foreign_component_id,
                            dependency_type=DependencyType.CALL,
                        ),
                    )

                updated = Dependency(
                    entity_id=dependency_id,
                    source_component_id=source_id,
                    target_component_id=target_id,
                    dependency_type=DependencyType.REFERENCE,
                    is_directed=False,
                    source_type=RelationOrigin.USER_DEFINED,
                    confidence=Decimal("1.0000"),
                    analysis_version="1.1",
                    analyzed_at=datetime.now(UTC),
                    metadata={"reviewed": True},
                )
                assert await repository.update(user_id, updated)
                stored = await repository.get_by_id(user_id, dependency_id)
                assert stored == updated
                assert stored is not None and stored.metadata == {"reviewed": True}
                assert await repository.delete(user_id, dependency_id)
                assert await repository.get_by_id(user_id, dependency_id) is None
            await transaction.rollback()
    finally:
        await engine.dispose()
