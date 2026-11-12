import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.domain.common.enums import EntityType, RelationOrigin, RelationType
from app.domain.relations import Relation as RelationEntity
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.projects.project import Project
from app.infrastructure.persistence.repositories.relations import (
    SqlAlchemyRelationRepository,
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
async def test_relation_repository_scopes_lifecycle_and_entity_references() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    other_user_id = uuid4()
    project_id = uuid4()
    other_project_id = uuid4()
    relation_id = uuid4()
    other_target_id = uuid4()
    now = datetime.now(UTC)
    relation = RelationEntity(
        entity_id=relation_id,
        project_id=project_id,
        source_entity_type=EntityType.PROJECT,
        source_entity_id=project_id,
        target_entity_type=EntityType.OTHER,
        target_entity_id=other_target_id,
        relation_type=RelationType.CONTAINS,
        origin=RelationOrigin.USER_DEFINED,
        confidence=None,
        metadata={"source": "integration"},
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
                session.add_all(
                    [
                        User(
                            id=owner_id,
                            email=f"{owner_id}@example.test",
                            display_name="Relation Repository Integration Test",
                            auth_provider="integration-test",
                        )
                        for owner_id in (user_id, other_user_id)
                    ]
                )
                session.add_all(
                    [
                        Project(
                            id=owner_project_id,
                            user_id=owner_id,
                            name="Relation Repository Integration Test",
                            slug=f"relation-repository-{owner_project_id}",
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

                repository = SqlAlchemyRelationRepository(session)
                assert await repository.project_exists(user_id, project_id)
                assert not await repository.project_exists(other_user_id, project_id)
                assert await repository.reference_belongs_to_project(
                    user_id, project_id, EntityType.PROJECT, project_id
                )
                assert await repository.reference_belongs_to_project(
                    user_id, project_id, EntityType.OTHER, other_target_id
                )
                assert not await repository.reference_belongs_to_project(
                    other_user_id, project_id, EntityType.PROJECT, project_id
                )

                await repository.create(user_id, relation)
                fetched = await repository.get_by_id(user_id, project_id, relation_id)
                assert fetched is not None
                assert fetched.metadata == {"source": "integration"}
                assert [
                    item.id for item in await repository.get_by_project(user_id, project_id)
                ] == [relation_id]
                assert await repository.get_by_project(
                    user_id, project_id, EntityType.OTHER, other_target_id
                ) == [fetched]
                assert (
                    await repository.get_by_id(other_user_id, project_id, relation_id)
                    is None
                )

                updated = RelationEntity(
                    entity_id=relation_id,
                    project_id=project_id,
                    source_entity_type=EntityType.PROJECT,
                    source_entity_id=project_id,
                    target_entity_type=EntityType.OTHER,
                    target_entity_id=other_target_id,
                    relation_type=RelationType.REFERENCES,
                    origin=RelationOrigin.USER_DEFINED,
                    confidence=None,
                    metadata={"updated": True},
                    created_at=now,
                    updated_at=now + timedelta(seconds=1),
                )
                assert await repository.update(user_id, updated)
                with pytest.raises(ValueError):
                    await repository.update(other_user_id, updated)
                stored = await repository.get_by_id(user_id, project_id, relation_id)
                assert stored is not None
                assert stored.relation_type is RelationType.REFERENCES
                assert stored.metadata == {"updated": True}
                assert not await repository.delete(other_user_id, project_id, relation_id)
                assert await repository.delete(user_id, project_id, relation_id)
                assert await repository.get_by_id(user_id, project_id, relation_id) is None
            await transaction.rollback()
    finally:
        await engine.dispose()
