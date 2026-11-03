from copy import deepcopy
from datetime import datetime
from typing import Any
from uuid import UUID

from ...common.entity import Entity
from ...common.types import EntityId
from ..enums import ExecutionStatus
from ..exceptions import InvalidScriptExecution


class ScriptExecution(Entity):
    """Execution metadata and sanitized results. Full command output remains local."""

    def __init__(
        self,
        entity_id: EntityId,
        script_id: EntityId,
        client_device_id: EntityId,
        created_at: datetime,
        device_id: EntityId | None = None,
        parameters: Any | None = None,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        exit_code: int | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
        error_message: str | None = None,
        sanitized_output_summary: str | None = None,
        idempotency_key: EntityId | None = None,
    ) -> None:
        if not isinstance(entity_id, UUID):
            raise InvalidScriptExecution("Execution identifier must be a UUID")
        if not isinstance(script_id, UUID) or not isinstance(client_device_id, UUID):
            raise InvalidScriptExecution(
                "Script and client device identifiers must be UUIDs"
            )
        if device_id is not None and not isinstance(device_id, UUID):
            raise InvalidScriptExecution("Device identifier must be a UUID")
        if idempotency_key is not None and not isinstance(idempotency_key, UUID):
            raise InvalidScriptExecution("Idempotency key must be a UUID")
        if not isinstance(status, ExecutionStatus):
            raise InvalidScriptExecution("Execution status is invalid")
        if exit_code is not None and (
            not isinstance(exit_code, int) or isinstance(exit_code, bool)
        ):
            raise InvalidScriptExecution("Exit code must be an integer")
        if error_message is not None and not isinstance(error_message, str):
            raise InvalidScriptExecution("Error message must be a string")
        if sanitized_output_summary is not None and not isinstance(
            sanitized_output_summary, str
        ):
            raise InvalidScriptExecution("Output summary must be a string")

        self._validate_timestamp(created_at, "created_at")
        if started_at is not None:
            self._validate_timestamp(started_at, "started_at")
            if started_at < created_at:
                raise InvalidScriptExecution(
                    "Start time cannot precede execution creation"
                )
        if finished_at is not None:
            self._validate_timestamp(finished_at, "finished_at")
            if finished_at < created_at:
                raise InvalidScriptExecution(
                    "Finish time cannot precede execution creation"
                )
        if (
            started_at is not None
            and finished_at is not None
            and finished_at < started_at
        ):
            raise InvalidScriptExecution("Finish time cannot precede start time")
        self._validate_status_consistency(
            status,
            started_at,
            finished_at,
            exit_code,
            error_message,
            sanitized_output_summary,
        )

        super().__init__(entity_id)
        self._script_id = script_id
        self._device_id = device_id
        self._client_device_id = client_device_id
        self._parameters = deepcopy(parameters)
        self._status = status
        self._exit_code = exit_code
        self._started_at = started_at
        self._finished_at = finished_at
        self._error_message = error_message
        self._sanitized_output_summary = sanitized_output_summary
        self._idempotency_key = idempotency_key
        self._created_at = created_at

    @staticmethod
    def _validate_timestamp(value: datetime, name: str) -> None:
        if not isinstance(value, datetime) or value.utcoffset() is None:
            raise InvalidScriptExecution(f"Execution {name} must include a timezone")

    @staticmethod
    def _validate_status_consistency(
        status: ExecutionStatus,
        started_at: datetime | None,
        finished_at: datetime | None,
        exit_code: int | None,
        error_message: str | None,
        sanitized_output_summary: str | None,
    ) -> None:
        if status is ExecutionStatus.PENDING and any(
            value is not None
            for value in (
                started_at,
                finished_at,
                exit_code,
                error_message,
                sanitized_output_summary,
            )
        ):
            raise InvalidScriptExecution(
                "Pending execution cannot contain start or result data"
            )
        if status is ExecutionStatus.RUNNING and (
            started_at is None or finished_at is not None or exit_code is not None
        ):
            raise InvalidScriptExecution(
                "Running execution requires a start time and no final result"
            )
        if (
            status
            in (
                ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
                ExecutionStatus.TIMEOUT,
            )
            and finished_at is None
        ):
            raise InvalidScriptExecution("Finished execution requires a finish time")
        if status is ExecutionStatus.COMPLETED and started_at is None:
            raise InvalidScriptExecution("Completed execution requires a start time")

    def start(self, at: datetime) -> None:
        if self._status is not ExecutionStatus.PENDING:
            raise InvalidScriptExecution("Only pending executions can be started")
        self._validate_timestamp(at, "started_at")
        if at < self._created_at:
            raise InvalidScriptExecution("Start time cannot precede execution creation")
        self._started_at = at
        self._status = ExecutionStatus.RUNNING

    def complete(
        self,
        at: datetime,
        exit_code: int = 0,
        sanitized_output_summary: str | None = None,
    ) -> None:
        if self._status is not ExecutionStatus.RUNNING:
            raise InvalidScriptExecution("Only running executions can be completed")
        self._finish(
            ExecutionStatus.COMPLETED,
            at,
            exit_code,
            None,
            sanitized_output_summary,
        )

    def fail(
        self,
        at: datetime,
        error_message: str,
        exit_code: int | None = None,
        sanitized_output_summary: str | None = None,
    ) -> None:
        if self._status not in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING):
            raise InvalidScriptExecution("Only active executions can fail")
        self._finish(
            ExecutionStatus.FAILED,
            at,
            exit_code,
            error_message,
            sanitized_output_summary,
        )

    def cancel(self, at: datetime, error_message: str | None = None) -> None:
        if self._status not in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING):
            raise InvalidScriptExecution("Only active executions can be cancelled")
        self._finish(ExecutionStatus.CANCELLED, at, None, error_message, None)

    def timeout(
        self,
        at: datetime,
        error_message: str | None = None,
        exit_code: int | None = None,
        sanitized_output_summary: str | None = None,
    ) -> None:
        if self._status not in (ExecutionStatus.PENDING, ExecutionStatus.RUNNING):
            raise InvalidScriptExecution("Only active executions can time out")
        self._finish(
            ExecutionStatus.TIMEOUT,
            at,
            exit_code,
            error_message,
            sanitized_output_summary,
        )

    def _finish(
        self,
        status: ExecutionStatus,
        at: datetime,
        exit_code: int | None,
        error_message: str | None,
        sanitized_output_summary: str | None,
    ) -> None:
        self._validate_timestamp(at, "finished_at")
        if at < self._created_at:
            raise InvalidScriptExecution(
                "Finish time cannot precede execution creation"
            )
        if self._started_at is not None and at < self._started_at:
            raise InvalidScriptExecution("Finish time cannot precede start time")
        if exit_code is not None and (
            not isinstance(exit_code, int) or isinstance(exit_code, bool)
        ):
            raise InvalidScriptExecution("Exit code must be an integer")
        if error_message is not None and not isinstance(error_message, str):
            raise InvalidScriptExecution("Error message must be a string")
        if sanitized_output_summary is not None and not isinstance(
            sanitized_output_summary, str
        ):
            raise InvalidScriptExecution("Output summary must be a string")
        self._status = status
        self._finished_at = at
        self._exit_code = exit_code
        self._error_message = error_message
        self._sanitized_output_summary = sanitized_output_summary

    @property
    def script_id(self) -> EntityId:
        return self._script_id

    @property
    def device_id(self) -> EntityId | None:
        return self._device_id

    @property
    def client_device_id(self) -> EntityId:
        return self._client_device_id

    @property
    def parameters(self) -> Any | None:
        return deepcopy(self._parameters)

    @property
    def status(self) -> ExecutionStatus:
        return self._status

    @property
    def exit_code(self) -> int | None:
        return self._exit_code

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def finished_at(self) -> datetime | None:
        return self._finished_at

    @property
    def error_message(self) -> str | None:
        return self._error_message

    @property
    def sanitized_output_summary(self) -> str | None:
        return self._sanitized_output_summary

    @property
    def idempotency_key(self) -> EntityId | None:
        return self._idempotency_key

    @property
    def created_at(self) -> datetime:
        return self._created_at
