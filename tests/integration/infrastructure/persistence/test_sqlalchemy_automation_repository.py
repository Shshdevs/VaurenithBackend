import os
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.domain.automation import Script, ScriptExecution, ScriptTarget
from app.domain.automation.enums import (
    ExecutionStatus,
    ScriptExecutionType,
    ScriptRiskLevel,
)
from app.domain.identity.enums import PlatformType
from app.domain.infrastructure.enums import DeviceType
from app.infrastructure.persistence.models.identity.client_device import (
    ClientDevice as ClientDeviceModel,
)
from app.infrastructure.persistence.models.identity.user import User as UserModel
from app.infrastructure.persistence.models.infrastructure.device import (
    Device as DeviceModel,
)
from app.infrastructure.persistence.repositories.automation import (
    SqlAlchemyScriptExecutionRepository,
    SqlAlchemyScriptRepository,
    SqlAlchemyScriptTargetRepository,
)


def assert_test_database_is_separate(test_database_url: str) -> None:
    configured_database = make_url(get_settings().database_url)
    test_database = make_url(test_database_url)
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
async def test_automation_repository_persists_script_target_and_execution_lifecycle() -> (
    None
):
    test_database_url = os.environ.get("TEST_DATABASE_URL")
    if not test_database_url:
        pytest.skip("Set TEST_DATABASE_URL to run the PostgreSQL automation test")
    assert_test_database_is_separate(test_database_url)

    engine = create_async_engine(test_database_url)
    user_id = uuid4()
    device_id = uuid4()
    client_device_id = uuid4()
    script_id = uuid4()
    target_id = uuid4()
    execution_id = uuid4()
    now = datetime.now(UTC)
    script = Script(
        entity_id=script_id,
        name="Integration script",
        content="echo integration",
        execution_type=ScriptExecutionType.SSH,
        risk_level=ScriptRiskLevel.SAFE,
        created_at=now,
        updated_at=now,
    )
    target = ScriptTarget(
        entity_id=target_id,
        script_id=script_id,
        device_id=device_id,
        created_at=now,
    )
    execution = ScriptExecution(
        entity_id=execution_id,
        script_id=script_id,
        device_id=device_id,
        client_device_id=client_device_id,
        created_at=now,
    )

    try:
        async with engine.connect() as connection:
            transaction = await connection.begin()
            async with AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                expire_on_commit=False,
            ) as session:
                session.add(
                    UserModel(
                        id=user_id,
                        email=f"{user_id}@example.test",
                        auth_provider="automation-integration-test",
                        created_at=now,
                        updated_at=now,
                    )
                )
                session.add(
                    DeviceModel(
                        id=device_id,
                        user_id=user_id,
                        name="Automation target",
                        device_type=DeviceType.VIRTUAL,
                        created_at=now,
                        updated_at=now,
                    )
                )
                session.add(
                    ClientDeviceModel(
                        id=client_device_id,
                        user_id=user_id,
                        name="Automation agent",
                        platform=PlatformType.LINUX,
                        registered_at=now,
                        last_seen_at=now,
                    )
                )
                await session.flush()

                repository = SqlAlchemyScriptRepository(session)
                target_repository = SqlAlchemyScriptTargetRepository(session)
                execution_repository = SqlAlchemyScriptExecutionRepository(session)
                await repository.create_script(user_id, script)
                stored_script = await repository.get_script(user_id, script_id)
                assert stored_script is not None
                assert stored_script.content == "echo integration"
                assert await repository.get_script(uuid4(), script_id) is None

                await target_repository.create_target(user_id, target)
                assert await target_repository.get_targets(user_id, script_id) == [target]

                await execution_repository.create_execution(user_id, execution)
                pending = await execution_repository.get_pending_executions(
                    user_id, client_device_id
                )
                assert [item.id for item in pending] == [execution_id]

                execution.start(datetime.now(UTC))
                assert await execution_repository.update_execution(
                    user_id, execution, ExecutionStatus.PENDING
                )
                execution.complete(datetime.now(UTC), sanitized_output_summary="done")
                assert await execution_repository.update_execution(
                    user_id, execution, ExecutionStatus.RUNNING
                )
                stored_execution = await execution_repository.get_execution(
                    user_id, execution_id
                )
                assert stored_execution is not None
                assert stored_execution.status is ExecutionStatus.COMPLETED
                assert stored_execution.sanitized_output_summary == "done"
                assert (
                    await execution_repository.get_execution(uuid4(), execution_id) is None
                )
            await transaction.rollback()
    finally:
        await engine.dispose()
