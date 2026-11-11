import hashlib
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.domain.identity.entities.client_device import ClientDevice
from app.domain.identity.entities.session import Session
from app.domain.identity.entities.user import User
from app.domain.identity.enums import PlatformType
from app.domain.identity.value_objects.email import EmailAddress
from app.domain.identity.value_objects.token_hash import TokenHash
from app.infrastructure.persistence.repositories.identity import (
    SqlAlchemySessionRepository,
    SqlAlchemyUserRepository,
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
async def test_register_persists_user_and_session_then_rolls_back() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    now = datetime.now(UTC)
    token_hash = TokenHash(hashlib.sha256(str(uuid4()).encode()).hexdigest())
    user = User(
        entity_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        display_name="Repository Integration Test",
        auth_provider="integration-test",
        created_at=now,
        updated_at=now,
    )
    client_device = ClientDevice(
        entity_id=uuid4(),
        user_id=user_id,
        name="Repository Integration Test Device",
        platform=PlatformType.OTHER,
        registered_at=now,
    )
    session = Session(
        entity_id=uuid4(),
        user_id=user_id,
        token_hash=token_hash,
        expires_at=now + timedelta(hours=1),
        created_at=now,
        client_device_id=client_device.id,
    )

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            async with AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            ) as database_session:
                user_repository = SqlAlchemyUserRepository(database_session)
                session_repository = SqlAlchemySessionRepository(database_session)

                await user_repository.register(user, client_device, session)

                stored_user = await user_repository.get_by_id(user_id)
                assert stored_user is not None
                assert stored_user.email == user.email
                assert stored_user.display_name == user.display_name
                assert await session_repository.has_active_session(token_hash, now)
                assert session.client_device_id == client_device.id

                assert await user_repository.delete(user_id)
                assert await user_repository.get_by_id(user_id) is None

            await transaction.rollback()

        async with AsyncSession(engine) as verification_session:
            stored_user = await SqlAlchemyUserRepository(verification_session).get_by_id(
                user_id
            )
            assert stored_user is None
    finally:
        await engine.dispose()
