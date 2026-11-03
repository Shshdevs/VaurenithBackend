from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.domain.automation.entities.script_execution import ScriptExecution
from app.domain.automation.enums import ExecutionStatus
from app.domain.automation.exceptions import InvalidScriptExecution


def make_execution(**overrides: Any) -> ScriptExecution:
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "script_id": uuid4(),
        "client_device_id": uuid4(),
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return ScriptExecution(**values)


def test_script_execution_defaults_to_pending() -> None:
    execution = make_execution()

    assert execution.status is ExecutionStatus.PENDING
    assert execution.device_id is None
    assert execution.exit_code is None
    assert execution.started_at is None
    assert execution.finished_at is None


def test_script_execution_exposes_optional_values() -> None:
    device_id = uuid4()
    idempotency_key = uuid4()
    execution = make_execution(
        device_id=device_id,
        idempotency_key=idempotency_key,
        status=ExecutionStatus.COMPLETED,
        exit_code=0,
        started_at=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        finished_at=datetime(2026, 1, 1, 0, 2, tzinfo=UTC),
        sanitized_output_summary="Finished",
    )

    assert execution.device_id == device_id
    assert execution.idempotency_key == idempotency_key
    assert execution.status is ExecutionStatus.COMPLETED
    assert execution.exit_code == 0
    assert execution.sanitized_output_summary == "Finished"


def test_script_execution_parameters_are_defensively_copied() -> None:
    parameters = {"args": ["--quiet"]}
    expected = deepcopy(parameters)
    execution = make_execution(parameters=parameters)
    parameters["args"].append("--verbose")

    assert execution.parameters == expected
    returned_parameters = execution.parameters
    assert returned_parameters is not None
    returned_parameters["args"].append("--force")

    assert execution.parameters == expected


def test_script_execution_rejects_invalid_exit_code() -> None:
    with pytest.raises(InvalidScriptExecution):
        make_execution(exit_code=True)
    with pytest.raises(InvalidScriptExecution):
        make_execution(exit_code="0")


def test_script_execution_rejects_naive_timestamps() -> None:
    with pytest.raises(InvalidScriptExecution):
        make_execution(started_at=datetime(2026, 1, 1))


def test_script_execution_rejects_timestamps_before_creation() -> None:
    created_at = datetime(2026, 1, 1, 0, 1, tzinfo=UTC)

    with pytest.raises(InvalidScriptExecution):
        make_execution(
            created_at=created_at,
            started_at=created_at - timedelta(seconds=1),
        )


def test_script_execution_rejects_finish_before_start() -> None:
    started_at = datetime(2026, 1, 1, 0, 2, tzinfo=UTC)

    with pytest.raises(InvalidScriptExecution):
        make_execution(
            started_at=started_at,
            finished_at=started_at - timedelta(seconds=1),
        )
