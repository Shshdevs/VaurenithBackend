import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceGroupAlreadyExists
from app.core.config import get_settings
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import DeviceGroup, DeviceGroupName
from app.domain.infrastructure.enums import DeviceType
from app.infrastructure.persistence.models.identity.user import User
from app.infrastructure.persistence.models.infrastructure.device import Device
from app.infrastructure.persistence.models.infrastructure.device_group import (
    DeviceGroup as DeviceGroupModel,
)
from app.infrastructure.persistence.models.infrastructure.device_group_member import (
    DeviceGroupMember,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDeviceGroupRepository,
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


def make_identity(user_id) -> VerifiedIdentity:
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="integration-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("e" * 64),
    )


@pytest.mark.anyio
async def test_device_group_repository_crud_owner_scope_and_member_cascade() -> None:
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL repository test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    other_user_id = uuid4()
    group_id = uuid4()
    device_id = uuid4()
    now = datetime.now(UTC)
    identity = make_identity(user_id)
    other_identity = make_identity(other_user_id)
    group = DeviceGroup(
        entity_id=group_id,
        user_id=user_id,
        name=DeviceGroupName("Production"),
        description="Primary fleet",
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
            ) as database_session:
                database_session.add_all(
                    [
                        User(
                            id=user_id,
                            email=f"{user_id}@example.test",
                            display_name="Device Group Integration Test",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                        User(
                            id=other_user_id,
                            email=f"{other_user_id}@example.test",
                            display_name="Device Group Other User",
                            auth_provider="integration-test",
                            created_at=now,
                            updated_at=now,
                        ),
                    ]
                )
                database_session.add(
                    Device(
                        id=device_id,
                        user_id=user_id,
                        name="Group member test device",
                        slug=f"group-member-{device_id}",
                        device_type=DeviceType.VPS,
                        created_at=now,
                        updated_at=now,
                    )
                )
                await database_session.flush()

                repository = SqlAlchemyDeviceGroupRepository(database_session)
                await repository.create(group)

                stored = await repository.get_by_id(identity, group_id)
                assert stored is not None
                assert stored.name == "Production"
                assert stored.slug == "production"
                assert stored.user_id == user_id
                assert stored.description == "Primary fleet"
                assert await repository.get_by_id(other_identity, group_id) is None

                updated = DeviceGroup(
                    entity_id=group_id,
                    user_id=user_id,
                    name=DeviceGroupName("Staging"),
                    description="Staging fleet",
                    created_at=now,
                    updated_at=datetime.now(UTC) + timedelta(seconds=1),
                )
                assert await repository.update(identity, updated)
                assert not await repository.update(other_identity, updated)
                stored_model = await database_session.scalar(
                    select(DeviceGroupModel).where(DeviceGroupModel.id == group_id)
                )
                assert stored_model is not None
                assert stored_model.name == "Staging"
                assert stored_model.description == "Staging fleet"

                duplicate = DeviceGroup(
                    entity_id=uuid4(),
                    user_id=user_id,
                    name=DeviceGroupName("Staging"),
                    created_at=now,
                    updated_at=now,
                )
                with pytest.raises(DeviceGroupAlreadyExists):
                    async with database_session.begin_nested():
                        await repository.create(duplicate)

                database_session.add(
                    DeviceGroupMember(group_id=group_id, device_id=device_id)
                )
                await database_session.flush()
                assert await repository.delete(identity, group_id)
                assert not await repository.delete(identity, group_id)
                assert await repository.get_by_id(identity, group_id) is None
                assert (
                    await database_session.scalar(
                        select(DeviceGroupMember).where(
                            DeviceGroupMember.group_id == group_id
                        )
                    )
                    is None
                )

            await transaction.rollback()
    finally:
        await engine.dispose()
