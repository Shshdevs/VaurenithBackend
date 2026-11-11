from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.application.automation.dto import ScriptExecutionData
from app.application.automation.interfaces import (
    ScriptExecutionRepository,
    ScriptRepository,
)
from app.application.common.exceptions import Conflict, InvalidInput, NotFound
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.domain.automation import ScriptExecution
from app.domain.automation.enums import ExecutionStatus
from app.domain.automation.exceptions import InvalidScriptExecution


class ExecutionOperations:
    def __init__(
        self,
        scripts: ScriptRepository,
        repository: ScriptExecutionRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._scripts = scripts
        self._repository = repository
        self._unit_of_work = unit_of_work

    async def list(
        self, identity: VerifiedIdentity, script_id: UUID | None = None
    ) -> list[ScriptExecutionData]:
        if (
            script_id is not None
            and await self._scripts.get_script(identity.user_id, script_id) is None
        ):
            raise NotFound(f"Script {script_id} not found")
        return [
            ScriptExecutionData.from_execution(execution)
            for execution in await self._repository.get_executions(
                identity.user_id, script_id
            )
        ]

    async def get(
        self, identity: VerifiedIdentity, execution_id: UUID
    ) -> ScriptExecutionData:
        execution = await self._repository.get_execution(identity.user_id, execution_id)
        if execution is None:
            raise NotFound(f"Execution {execution_id} not found")
        return ScriptExecutionData.from_execution(execution)

    @transactional
    async def request(
        self,
        identity: VerifiedIdentity,
        script_id: UUID,
        client_device_id: UUID,
        device_id: UUID | None,
        parameters,
        idempotency_key: UUID | None,
        confirmed: bool,
    ) -> ScriptExecutionData:
        script = await self._scripts.get_script(identity.user_id, script_id)
        if script is None:
            raise NotFound(f"Script {script_id} not found")
        if script.requires_confirmation and not confirmed:
            raise InvalidInput("Script execution requires confirmation")
        if idempotency_key is not None:
            existing = await self._repository.get_execution_by_idempotency_key(
                identity.user_id, idempotency_key
            )
            if existing is not None:
                if (
                    existing.script_id != script_id
                    or existing.client_device_id != client_device_id
                ):
                    raise Conflict("Idempotency key was used for another execution")
                return ScriptExecutionData.from_execution(existing)
        try:
            execution = ScriptExecution(
                entity_id=uuid4(),
                script_id=script_id,
                client_device_id=client_device_id,
                device_id=device_id,
                parameters=parameters,
                idempotency_key=idempotency_key,
                created_at=datetime.now(UTC),
            )
        except InvalidScriptExecution as error:
            raise InvalidInput(str(error)) from error
        try:
            await self._repository.create_execution(identity.user_id, execution)
        except ValueError as error:
            raise Conflict(str(error)) from error
        return ScriptExecutionData.from_execution(execution)

    async def pending(
        self, identity: VerifiedIdentity, client_device_id: UUID
    ) -> list[ScriptExecutionData]:
        return [
            ScriptExecutionData.from_execution(execution)
            for execution in await self._repository.get_pending_executions(
                identity.user_id, client_device_id
            )
        ]

    @transactional
    async def start(
        self, identity: VerifiedIdentity, execution_id: UUID, client_device_id: UUID
    ) -> ScriptExecutionData:
        execution = await self._owned_execution(identity, execution_id, client_device_id)
        try:
            execution.start(datetime.now(UTC))
        except InvalidScriptExecution as error:
            raise Conflict(str(error)) from error
        if not await self._repository.update_execution(
            identity.user_id, execution, ExecutionStatus.PENDING
        ):
            raise Conflict("Execution is no longer pending")
        return ScriptExecutionData.from_execution(execution)

    @transactional
    async def finish(
        self,
        identity: VerifiedIdentity,
        execution_id: UUID,
        client_device_id: UUID,
        status: str,
        exit_code: int | None,
        error_message: str | None,
        sanitized_output_summary: str | None,
    ) -> ScriptExecutionData:
        execution = await self._owned_execution(identity, execution_id, client_device_id)
        expected_status = execution.status
        now = datetime.now(UTC)
        try:
            if status == "completed":
                execution.complete(
                    now,
                    0 if exit_code is None else exit_code,
                    sanitized_output_summary,
                )
            elif status == "failed":
                execution.fail(
                    now,
                    error_message or "Execution failed",
                    exit_code,
                    sanitized_output_summary,
                )
            elif status == "cancelled":
                execution.cancel(now, error_message)
            elif status == "timeout":
                execution.timeout(now, error_message, exit_code, sanitized_output_summary)
            else:
                raise InvalidInput("Execution result status is invalid")
        except InvalidScriptExecution as error:
            raise Conflict(str(error)) from error
        if not await self._repository.update_execution(
            identity.user_id, execution, expected_status
        ):
            raise Conflict("Execution is no longer active")
        return ScriptExecutionData.from_execution(execution)

    async def _owned_execution(
        self, identity: VerifiedIdentity, execution_id: UUID, client_device_id: UUID
    ) -> ScriptExecution:
        execution = await self._repository.get_execution(identity.user_id, execution_id)
        if execution is None or execution.client_device_id != client_device_id:
            raise NotFound(f"Execution {execution_id} not found")
        return execution
