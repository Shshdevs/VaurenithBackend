import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, insert, select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.application.common.exceptions import ChangeLogCursorExpired
from app.application.identity import VerifiedIdentity
from app.application.projects.use_cases.projects import CreateProject
from app.application.synchronization import RecordChange
from app.core.config import get_settings
from app.domain.common.enums import EntityType
from app.domain.identity import EmailAddress, TokenHash
from app.domain.projects import ProjectType
from app.domain.synchronization import ChangeLog, ChangeOperation
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.projects import Project as ProjectModel
from app.infrastructure.persistence.models.synchronization import (
    ChangeLog as ChangeLogModel,
)
from app.infrastructure.persistence.models.synchronization import (
    ChangeLogRetention,
)
from app.infrastructure.persistence.repositories.projects import (
    SqlAlchemyProjectRepository,
)
from app.infrastructure.persistence.repositories.synchronization import (
    SqlAlchemyChangeLogRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


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


def make_identity(user_id) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="change-log-integration-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_change(
    user_id, entity_id, version: int = 1, created_at: datetime | None = None
) -> ChangeLog:
    return ChangeLog(
        change_log_id=uuid4(),
        user_id=user_id,
        entity_type=EntityType.DEVICE,
        entity_id=entity_id,
        operation=ChangeOperation.INSERT,
        version=version,
        changed_by_user_id=user_id,
        created_at=created_at or datetime.now(UTC),
        payload={"name": "integration-device"},
    )


@pytest.mark.anyio
async def test_change_log_repository_persists_and_scopes_entries_by_user() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    other_user_id = uuid4()
    entity_id = uuid4()
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
                            id=user_id,
                            email=f"{user_id}@example.test",
                            display_name="Change Log Integration Test",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                        User(
                            id=other_user_id,
                            email=f"{other_user_id}@example.test",
                            display_name="Change Log Other Owner",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                await session.flush()

                repository = SqlAlchemyChangeLogRepository(session)
                await repository.create(make_change(user_id, entity_id))

                changes = await repository.get_by_user(user_id, after_sequence=0, limit=100)
                assert len(changes) == 1
                assert changes[0].entity_id == entity_id
                assert changes[0].sequence is not None
                assert changes[0].payload == {"name": "integration-device"}
                assert await repository.get_by_user(other_identity.user_id, 0, 100) == []
                assert (
                    await repository.get_by_user(identity.user_id, changes[0].sequence, 100)
                    == []
                )

            await transaction.rollback()
            assert (
                await connection.scalar(
                    select(User.id).where(User.id.in_([user_id, other_user_id]))
                )
                is None
            )
    finally:
        await engine.dispose()


@pytest.mark.anyio
async def test_change_log_sequence_follows_commit_order_for_same_user() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    entity_ids = (uuid4(), uuid4())
    now = datetime.now(UTC)
    second_started = asyncio.Event()
    user_created = False

    first_session = None
    second_session = None
    second_task = None
    try:
        async with engine.begin() as connection:
            await connection.execute(
                insert(User).values(
                    id=user_id,
                    email=f"{user_id}@example.test",
                    display_name="Change Log Ordering Test",
                    auth_provider="integration-test",
                    created_at=now,
                    updated_at=now,
                )
            )
        user_created = True

        first_session = AsyncSession(engine, expire_on_commit=False)
        second_session = AsyncSession(engine, expire_on_commit=False)
        await first_session.begin()
        await second_session.begin()
        first_repository = SqlAlchemyChangeLogRepository(first_session)
        second_repository = SqlAlchemyChangeLogRepository(second_session)
        await first_repository.create(make_change(user_id, entity_ids[0]))

        async def write_second_change() -> None:
            second_started.set()
            await second_repository.create(make_change(user_id, entity_ids[1]))

        second_task = asyncio.create_task(write_second_change())
        await second_started.wait()
        await asyncio.sleep(0.05)
        assert not second_task.done()

        await first_session.commit()
        await second_task
        await second_session.commit()

        async with AsyncSession(engine) as session:
            repository = SqlAlchemyChangeLogRepository(session)
            changes = await repository.get_by_user(user_id, 0, 100)
            assert [change.entity_id for change in changes] == list(entity_ids)
            assert changes[0].sequence is not None
            assert changes[1].sequence is not None
            assert changes[0].sequence < changes[1].sequence

    finally:
        if second_task is not None and not second_task.done():
            second_task.cancel()
            await asyncio.gather(second_task, return_exceptions=True)
        if first_session is not None:
            if first_session.in_transaction():
                await first_session.rollback()
            await first_session.close()
        if second_session is not None:
            if second_session.in_transaction():
                await second_session.rollback()
            await second_session.close()
        if user_created:
            async with engine.begin() as connection:
                await connection.execute(
                    delete(ChangeLogModel).where(ChangeLogModel.user_id == user_id)
                )
                await connection.execute(delete(User).where(User.id == user_id))
        await engine.dispose()


@pytest.mark.anyio
async def test_project_and_change_log_share_transaction() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    project_id = None
    user_created = False
    now = datetime.now(UTC)

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
                        display_name="Change Log Atomicity Test",
                        auth_provider="integration-test",
                        created_at=now,
                        updated_at=now,
                    )
                )
                await session.flush()
                user_created = True
                identity = make_identity(user_id)
                use_case = CreateProject(
                    SqlAlchemyProjectRepository(session),
                    RecordChange(SqlAlchemyChangeLogRepository(session)),
                    SqlAlchemyUnitOfWork(session),
                )

                project = await use_case.execute(
                    identity,
                    name="Atomic Change Log Project",
                    project_type=ProjectType.SOFTWARE,
                )
                project_id = project.id

                assert (
                    await session.scalar(
                        select(ChangeLogModel.id).where(
                            ChangeLogModel.entity_id == project_id
                        )
                    )
                    is not None
                )
                assert (
                    await session.scalar(
                        select(ProjectModel.id).where(ProjectModel.id == project_id)
                    )
                    is not None
                )

            await transaction.rollback()
            assert (
                await connection.scalar(
                    select(ProjectModel.id).where(ProjectModel.id == project_id)
                )
                is None
            )
            assert (
                await connection.scalar(
                    select(ChangeLogModel.id).where(ChangeLogModel.entity_id == project_id)
                )
                is None
            )
    finally:
        if user_created:
            async with engine.begin() as connection:
                await connection.execute(
                    delete(ChangeLogModel).where(ChangeLogModel.user_id == user_id)
                )
                if project_id is not None:
                    await connection.execute(
                        delete(ProjectModel).where(ProjectModel.id == project_id)
                    )
                await connection.execute(delete(User).where(User.id == user_id))
        await engine.dispose()


@pytest.mark.anyio
async def test_expired_change_log_entries_are_pruned_and_require_resync() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    old_entity_id, current_entity_id = uuid4(), uuid4()
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=365)

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
                        display_name="Change Log Retention Test",
                        auth_provider="integration-test",
                        created_at=now,
                        updated_at=now,
                    )
                )
                await session.flush()
                repository = SqlAlchemyChangeLogRepository(session)
                await repository.create(
                    make_change(
                        user_id,
                        old_entity_id,
                        created_at=now - timedelta(days=366),
                    )
                )
                await repository.create(make_change(user_id, current_entity_id))

                assert await repository.purge_expired(cutoff) == 1
                expired_through_sequence = await session.scalar(
                    select(ChangeLogRetention.expired_through_sequence).where(
                        ChangeLogRetention.user_id == user_id
                    )
                )
                assert expired_through_sequence is not None
                with pytest.raises(ChangeLogCursorExpired) as error:
                    await repository.get_by_user(user_id, after_sequence=0, limit=100)
                assert error.value.restart_sequence > expired_through_sequence

                changes = await repository.get_by_user(
                    user_id,
                    after_sequence=expired_through_sequence,
                    limit=100,
                )
                assert [change.entity_id for change in changes] == [current_entity_id]

            await transaction.rollback()
    finally:
        await engine.dispose()
