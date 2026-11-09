import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.application.identity import VerifiedIdentity
from app.core.config import get_settings
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import Device, DeviceName, OperatingSystem
from app.domain.infrastructure.enums import DeviceType
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.infrastructure.device import (
    Device as DeviceModel,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDeviceRepository,
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


def make_identity(user_id) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="device-integration-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("f" * 64),
    )


@pytest.mark.anyio
async def test_device_repository_crud_owner_scope_and_soft_delete() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    other_user_id = uuid4()
    device_id = uuid4()
    now = datetime.now(UTC)
    identity = make_identity(user_id)
    other_identity = make_identity(other_user_id)
    device = Device(
        entity_id=device_id,
        user_id=user_id,
        name=DeviceName("worker-01"),
        created_at=now,
        updated_at=now,
        device_type=DeviceType.VPS,
        hostname="worker-01.internal",
        description="Production worker",
        operating_system_info=OperatingSystem("Linux", "6.1", "x86_64"),
        tags=["production"],
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
                            id=user_id,
                            email=f"{user_id}@example.test",
                            display_name="Device Integration Test",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                        User(
                            id=other_user_id,
                            email=f"{other_user_id}@example.test",
                            display_name="Device Other Owner",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                await session.flush()

                repository = SqlAlchemyDeviceRepository(session)
                await repository.create(device)
                stored = await repository.get_by_id(identity, device_id)
                assert stored is not None
                assert stored.name == "worker-01"
                assert stored.slug == "worker-01"
                assert stored.operating_system_info == OperatingSystem(
                    "Linux", "6.1", "x86_64"
                )
                assert stored.tags == ["production"]
                assert await repository.get_by_id(other_identity, device_id) is None
                assert [item.id for item in await repository.get_by_user(identity)] == [
                    device_id
                ]
                assert await repository.get_by_user(other_identity) == []

                updated = Device(
                    entity_id=device_id,
                    user_id=user_id,
                    name=DeviceName("worker-02"),
                    created_at=now,
                    updated_at=datetime.now(UTC) + timedelta(seconds=1),
                    device_type=DeviceType.CLOUD,
                    hostname="worker-02.internal",
                    operating_system_info=OperatingSystem("Linux", "6.2", "x86_64"),
                    tags=["staging"],
                    version=2,
                )
                assert await repository.update(identity, updated)
                assert not await repository.update(other_identity, updated)
                updated_model = await session.scalar(
                    select(DeviceModel).where(DeviceModel.id == device_id)
                )
                assert updated_model is not None
                assert updated_model.name == "worker-02"
                assert updated_model.version == 2

                deleted_at = datetime.now(UTC) + timedelta(seconds=2)
                assert await repository.delete(identity, device_id, deleted_at)
                assert not await repository.delete(identity, device_id, deleted_at)
                assert await repository.get_by_id(identity, device_id) is None
                assert await repository.get_by_user(identity) == []
                retained_model = await session.scalar(
                    select(DeviceModel).where(DeviceModel.id == device_id)
                )
                assert retained_model is not None
                assert retained_model.deleted_at == deleted_at

            await transaction.rollback()
    finally:
        await engine.dispose()
