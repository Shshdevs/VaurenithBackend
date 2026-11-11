from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import exists, select, update

from app.domain.automation import ScriptExecution
from app.domain.automation.enums import ExecutionStatus
from app.infrastructure.persistence.models.automation import Script as ScriptModel
from app.infrastructure.persistence.models.automation import (
    ScriptExecution as ExecutionModel,
)
from app.infrastructure.persistence.models.automation import ScriptTarget as TargetModel
from app.infrastructure.persistence.models.identity.client_device import ClientDevice
from app.infrastructure.persistence.models.infrastructure.device import Device

from .sqlalchemy_automation_repository_base import (
    SqlAlchemyAutomationRepositoryBase,
)


class SqlAlchemyScriptExecutionRepository(SqlAlchemyAutomationRepositoryBase):
    async def create_execution(self, user_id: UUID, execution: ScriptExecution) -> None:
        script_exists = await self._session.scalar(
            select(ScriptModel.id).where(
                ScriptModel.id == execution.script_id,
                ScriptModel.deleted_at.is_(None),
                self._owned_script(user_id),
            )
        )
        if script_exists is None:
            raise ValueError("Script not found")
        client_owned = await self._session.scalar(
            select(ClientDevice.id).where(
                ClientDevice.id == execution.client_device_id,
                ClientDevice.user_id == user_id,
                ClientDevice.status == "active",
            )
        )
        if client_owned is None:
            raise ValueError("Active client device not found")
        if execution.device_id is not None:
            device_owned = await self._session.scalar(
                select(Device.id).where(
                    Device.id == execution.device_id, Device.user_id == user_id
                )
            )
            if device_owned is None:
                raise ValueError("Device not found")
            assigned = await self._session.scalar(
                select(TargetModel.id).where(
                    TargetModel.script_id == execution.script_id,
                    TargetModel.device_id == execution.device_id,
                )
            )
            if assigned is None:
                raise ValueError("Script is not assigned to this device")
        self._session.add(self._to_execution_model(execution))

    async def get_execution(
        self, user_id: UUID, execution_id: UUID
    ) -> ScriptExecution | None:
        result = await self._session.execute(
            select(ExecutionModel)
            .join(ScriptModel, ScriptModel.id == ExecutionModel.script_id)
            .where(ExecutionModel.id == execution_id, self._owned_script(user_id))
        )
        model = result.scalar_one_or_none()
        return self._to_execution(model) if model is not None else None

    async def get_execution_by_idempotency_key(
        self, user_id: UUID, idempotency_key: UUID
    ) -> ScriptExecution | None:
        result = await self._session.execute(
            select(ExecutionModel)
            .join(ScriptModel, ScriptModel.id == ExecutionModel.script_id)
            .where(
                ExecutionModel.idempotency_key == idempotency_key,
                self._owned_script(user_id),
            )
        )
        model = result.scalar_one_or_none()
        return self._to_execution(model) if model is not None else None

    async def get_pending_executions(
        self, user_id: UUID, client_device_id: UUID
    ) -> list[ScriptExecution]:
        result = await self._session.execute(
            select(ExecutionModel)
            .join(ScriptModel, ScriptModel.id == ExecutionModel.script_id)
            .where(
                ExecutionModel.client_device_id == client_device_id,
                ExecutionModel.status == ExecutionStatus.PENDING,
                ScriptModel.deleted_at.is_(None),
                exists(
                    select(ClientDevice.id).where(
                        ClientDevice.id == client_device_id,
                        ClientDevice.user_id == user_id,
                        ClientDevice.status == "active",
                    )
                ),
                self._owned_script(user_id),
            )
            .order_by(ExecutionModel.created_at, ExecutionModel.id)
        )
        return [self._to_execution(row) for row in result.scalars().all()]

    async def get_executions(
        self, user_id: UUID, script_id: UUID | None = None
    ) -> list[ScriptExecution]:
        statement = (
            select(ExecutionModel)
            .join(ScriptModel, ScriptModel.id == ExecutionModel.script_id)
            .where(self._owned_script(user_id))
            .order_by(ExecutionModel.created_at.desc(), ExecutionModel.id)
        )
        if script_id is not None:
            statement = statement.where(ExecutionModel.script_id == script_id)
        result = await self._session.execute(statement)
        return [self._to_execution(row) for row in result.scalars().all()]

    async def update_execution(
        self, user_id: UUID, execution: ScriptExecution, expected_status: ExecutionStatus
    ) -> bool:
        result = await self._session.execute(
            update(ExecutionModel)
            .where(
                ExecutionModel.id == execution.id,
                ExecutionModel.client_device_id == execution.client_device_id,
                ExecutionModel.status == expected_status,
                exists(
                    select(ScriptModel.id).where(
                        ScriptModel.id == ExecutionModel.script_id,
                        self._owned_script(user_id),
                    )
                ),
            )
            .values(
                status=execution.status,
                exit_code=execution.exit_code,
                started_at=execution.started_at,
                finished_at=execution.finished_at,
                error_message=execution.error_message,
                sanitized_output_summary=execution.sanitized_output_summary,
            )
            .returning(ExecutionModel.id)
        )
        return result.scalar_one_or_none() is not None

    async def cancel_pending_for_script(self, user_id: UUID, script_id: UUID) -> None:
        now = datetime.now(UTC)
        await self._session.execute(
            update(ExecutionModel)
            .where(
                ExecutionModel.script_id == script_id,
                ExecutionModel.status == ExecutionStatus.PENDING,
                exists(
                    select(ScriptModel.id).where(
                        ScriptModel.id == script_id, self._owned_script(user_id)
                    )
                ),
            )
            .values(
                status=ExecutionStatus.CANCELLED,
                finished_at=now,
                error_message="Script was deleted before execution",
            )
        )
