from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.automation.enums import ExecutionStatus


@dataclass(frozen=True, slots=True)
class ScriptExecutionData:
    id: UUID
    script_id: UUID
    device_id: UUID | None
    client_device_id: UUID
    parameters: Any | None
    status: ExecutionStatus
    exit_code: int | None
    started_at: datetime | None
    finished_at: datetime | None
    error_message: str | None
    sanitized_output_summary: str | None
    idempotency_key: UUID | None
    created_at: datetime

    @classmethod
    def from_execution(cls, execution) -> "ScriptExecutionData":
        return cls(
            id=execution.id,
            script_id=execution.script_id,
            device_id=execution.device_id,
            client_device_id=execution.client_device_id,
            parameters=execution.parameters,
            status=execution.status,
            exit_code=execution.exit_code,
            started_at=execution.started_at,
            finished_at=execution.finished_at,
            error_message=execution.error_message,
            sanitized_output_summary=execution.sanitized_output_summary,
            idempotency_key=execution.idempotency_key,
            created_at=execution.created_at,
        )
