import asyncio
import hashlib
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.application.identity.dto import VerifiedIdentity
from app.application.identity.use_cases import CreateDeviceSession, RevokeClientDevice
from app.core.config import get_settings
from app.domain.identity import (
    ClientDevice,
    EmailAddress,
    PlatformType,
    TokenHash,
)
from app.domain.identity import (
    Session as SessionEntity,
)
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.repositories.identity import (
    SqlAlchemyClientDeviceRepository,
    SqlAlchemySessionRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def assert_test_database_is_separate(test_database_url: str) -> None:
    configured = make_url(get_settings().database_url)
    test_database = make_url(test_database_url)
    if (
        test_database.drivername,
        test_database.host,
        test_database.port,
        test_database.database,
    ) == (configured.drivername, configured.host, configured.port, configured.database):
        pytest.fail("TEST_DATABASE_URL must point to a separate database")


def make_identity(user_id, token: str) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="device-lifecycle-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash(hashlib.sha256(token.encode()).hexdigest()),
    )


async def create_test_owner(engine, user_id, device_id) -> None:
    now = datetime.now(UTC)
    async with AsyncSession(engine) as session, session.begin():
        session.add(
            User(
                id=user_id,
                email=f"{user_id}@example.test",
                display_name="Client device lifecycle test",
                nickname=f"client-device-{user_id.hex[:8]}",
                auth_provider="device-lifecycle-test",
                created_at=now,
                updated_at=now,
            )
        )
        device = ClientDevice(
            entity_id=device_id,
            user_id=user_id,
            name="Lifecycle test device",
            platform=PlatformType.OTHER,
            registered_at=now,
        )
        await SqlAlchemyClientDeviceRepository(session).create(device)


async def cleanup_test_owner(engine, user_id) -> None:
    from sqlalchemy import delete

    from app.infrastructure.persistence.models.identity.client_device import (
        ClientDevice as ClientDeviceModel,
    )
    from app.infrastructure.persistence.models.identity.session import Session

    async with AsyncSession(engine) as session, session.begin():
        await session.execute(delete(Session).where(Session.user_id == user_id))
        await session.execute(
            delete(ClientDeviceModel).where(ClientDeviceModel.user_id == user_id)
        )
        await session.execute(delete(User).where(User.id == user_id))


@pytest.mark.anyio
async def test_authentication_requires_active_device_and_revoke_blocks_token() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL identity test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id, device_id = uuid4(), uuid4()
    identity = make_identity(user_id, "active-test-token")
    now = datetime.now(UTC)
    try:
        await create_test_owner(engine, user_id, device_id)
        async with AsyncSession(engine) as session, session.begin():
            session_repository = SqlAlchemySessionRepository(session)
            await session_repository.create(
                SessionEntity(
                    entity_id=uuid4(),
                    user_id=user_id,
                    client_device_id=device_id,
                    token_hash=identity.token_hash,
                    expires_at=identity.expires_at,
                    created_at=now,
                )
            )
        async with AsyncSession(engine) as session, session.begin():
            session_repository = SqlAlchemySessionRepository(session)
            assert await session_repository.has_active_session(
                user_id, identity.token_hash, datetime.now(UTC)
            )
            await RevokeClientDevice(
                SqlAlchemyClientDeviceRepository(session),
                session_repository,
                SqlAlchemyUnitOfWork(session),
            ).execute(identity, device_id)
            assert not await session_repository.has_active_session(
                user_id, identity.token_hash, datetime.now(UTC)
            )
    finally:
        await cleanup_test_owner(engine, user_id)
        await engine.dispose()


@pytest.mark.anyio
async def test_session_creation_and_device_revoke_are_serialized() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL concurrency test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id, device_id = uuid4(), uuid4()
    identity = make_identity(user_id, "concurrent-device-token")
    locked = asyncio.Event()
    allow_create_to_commit = asyncio.Event()
    revoke_started = asyncio.Event()

    try:
        await create_test_owner(engine, user_id, device_id)

        async def create_session() -> None:
            async with AsyncSession(engine) as session, session.begin():
                use_case = CreateDeviceSession(
                    SqlAlchemyClientDeviceRepository(session),
                    SqlAlchemySessionRepository(session),
                    SqlAlchemyUnitOfWork(session),
                )
                repository = SqlAlchemyClientDeviceRepository(session)
                await repository.get_owned(user_id, device_id, for_update=True)
                locked.set()
                await allow_create_to_commit.wait()
                await use_case.execute(identity, device_id)

        async def revoke_device() -> None:
            await locked.wait()
            async with AsyncSession(engine) as session, session.begin():
                revoke_started.set()
                await RevokeClientDevice(
                    SqlAlchemyClientDeviceRepository(session),
                    SqlAlchemySessionRepository(session),
                    SqlAlchemyUnitOfWork(session),
                ).execute(identity, device_id)

        create_task = asyncio.create_task(create_session())
        await locked.wait()
        revoke_task = asyncio.create_task(revoke_device())
        await revoke_started.wait()
        await asyncio.sleep(0.05)
        allow_create_to_commit.set()
        await asyncio.gather(create_task, revoke_task)

        async with AsyncSession(engine) as session:
            assert not await SqlAlchemySessionRepository(session).has_active_session(
                user_id, identity.token_hash, datetime.now(UTC)
            )
    finally:
        allow_create_to_commit.set()
        await cleanup_test_owner(engine, user_id)
        await engine.dispose()
