from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema
from app.api.schemas.v1.automation.scripts import ScriptData
from app.domain.automation.enums import (
    ExecutionStatus,
)


class ScriptExecutionData(Schema):
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


class ScriptExecutionRequest(Schema):
    client_device_id: UUID
    device_id: UUID | None = None
    parameters: Any | None = None
    idempotency_key: UUID | None = None
    confirmed: bool = False


class ScriptExecutionStartRequest(Schema):
    client_device_id: UUID


class ScriptExecutionResultRequest(Schema):
    client_device_id: UUID
    status: ExecutionStatus
    exit_code: int | None = None
    error_message: str | None = Field(default=None, max_length=4000)
    sanitized_output_summary: str | None = Field(default=None, max_length=4000)


class ScriptExecutionQueueItem(Schema):
    execution: ScriptExecutionData
    script: ScriptData
