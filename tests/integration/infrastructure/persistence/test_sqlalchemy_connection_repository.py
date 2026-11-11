import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from tests.support_connections import make_connection

from app.application.identity import VerifiedIdentity
from app.core.config import get_settings
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure.enums import AuthenticationType, ConnectionStatus, DeviceType
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.infrastructure.connection import (
    Connection as ConnectionModel,
)
from app.infrastructure.persistence.models.infrastructure.device import (
    Device as DeviceModel,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyConnectionRepository,
)


def make_identity(user_id) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="connection-integration-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("b" * 64),
    )


@pytest.mark.anyio
async def test_connection_repository_enforces_ownership_versions_and_status() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    configured_url = make_url(get_settings().database_url)
    test_url = make_url(test_database_url)
    if (test_url.drivername, test_url.host, test_url.port, test_url.database) == (
        configured_url.drivername,
        configured_url.host,
        configured_url.port,
        configured_url.database,
    ):
        pytest.fail("TEST_DATABASE_URL must point to a separate database")

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    other_user_id = uuid4()
    device_id = uuid4()
    other_device_id = uuid4()
    deleted_device_id = uuid4()
    connection_id = uuid4()
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
                            id=owner_id,
                            email=f"{owner_id}@example.test",
                            display_name="Connection Integration Test",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        )
                        for owner_id in (user_id, other_user_id)
                    ]
                )
                session.add_all(
                    [
                        DeviceModel(
                            id=owned_device_id,
                            user_id=owner_id,
                            name=f"device-{owned_device_id.hex[:8]}",
                            device_type=DeviceType.VPS,
                            version=1,
                            created_at=now,
                            updated_at=now,
                            deleted_at=(
                                now if owned_device_id == deleted_device_id else None
                            ),
                        )
                        for owned_device_id, owner_id in (
                            (device_id, user_id),
                            (other_device_id, other_user_id),
                            (deleted_device_id, user_id),
                        )
                    ]
                )
                await session.flush()
                repository = SqlAlchemyConnectionRepository(session)
                created = make_connection(
                    device_id,
                    connection_id=connection_id,
                    now=now,
                    is_default=True,
                )

                assert await repository.create(identity, created)
                stored = await repository.get_by_id(identity, connection_id)
                assert stored is not None
                assert stored.name == created.name
                assert stored.slug == "primary-ssh"
                assert stored.authentication_type is AuthenticationType.SSH_KEY
                assert await repository.get_by_id(other_identity, connection_id) is None
                assert [item.id for item in await repository.get_by_user(identity)] == [
                    connection_id
                ]
                assert [
                    item.id for item in await repository.get_by_device(identity, device_id)
                ] == [connection_id]
                assert await repository.get_by_device(other_identity, device_id) == []
                assert await repository.get_by_device(identity, deleted_device_id) == []
                assert not await repository.create(
                    other_identity,
                    make_connection(device_id, now=now),
                )

                updated_at = now + timedelta(seconds=1)
                updated = make_connection(
                    device_id,
                    connection_id=connection_id,
                    name="Production SSH",
                    version=2,
                    now=updated_at,
                    is_default=True,
                )
                assert await repository.update(identity, updated, expected_version=1)
                assert not await repository.update(identity, created, expected_version=1)
                assert not await repository.update(
                    other_identity, updated, expected_version=2
                )

                connected_at = updated_at + timedelta(seconds=1)
                assert await repository.update_status(
                    identity,
                    connection_id,
                    2,
                    ConnectionStatus.CONNECTED,
                    connected_at,
                    "diagnostic error",
                    connected_at,
                )
                persisted = await session.scalar(
                    select(ConnectionModel).where(ConnectionModel.id == connection_id)
                )
                assert persisted is not None
                assert persisted.version == 3
                assert persisted.last_status is ConnectionStatus.CONNECTED
                assert persisted.last_error == "diagnostic error"
                assert not await repository.update_status(
                    other_identity,
                    connection_id,
                    3,
                    ConnectionStatus.FAILED,
                    connected_at,
                    None,
                    connected_at,
                )

                assert await repository.delete(identity, connection_id)
                assert not await repository.delete(identity, connection_id)
                await transaction.rollback()
    finally:
        await engine.dispose()
