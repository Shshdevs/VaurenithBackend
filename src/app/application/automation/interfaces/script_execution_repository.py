from typing import Protocol
from uuid import UUID

from app.domain.automation import ScriptExecution
from app.domain.automation.enums import ExecutionStatus


class ScriptExecutionRepository(Protocol):
    async def create_execution(self, user_id: UUID, execution: ScriptExecution) -> None: ...
    async def get_execution(
        self, user_id: UUID, execution_id: UUID
    ) -> ScriptExecution | None: ...
    async def get_execution_by_idempotency_key(
        self, user_id: UUID, idempotency_key: UUID
    ) -> ScriptExecution | None: ...
    async def get_executions(
        self, user_id: UUID, script_id: UUID | None = None
    ) -> list[ScriptExecution]: ...
    async def get_pending_executions(
        self, user_id: UUID, client_device_id: UUID
    ) -> list[ScriptExecution]: ...
    async def update_execution(
        self, user_id: UUID, execution: ScriptExecution, expected_status: ExecutionStatus
    ) -> bool: ...
    async def cancel_pending_for_script(self, user_id: UUID, script_id: UUID) -> None: ...
