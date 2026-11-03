from copy import deepcopy
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.domain.automation.entities.script import Script
from app.domain.automation.enums import ScriptExecutionType, ScriptRiskLevel
from app.domain.automation.exceptions import InvalidScript


def make_script(**overrides: Any) -> Script:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "name": "  Backup  ",
        "content": "#!/bin/sh\necho backup",
        "execution_type": ScriptExecutionType.LOCAL,
        "created_at": created_at,
        "updated_at": created_at,
    }
    values.update(overrides)
    return Script(**values)


def test_script_normalizes_name_and_sets_defaults() -> None:
    script = make_script()

    assert script.name == "Backup"
    assert script.execution_type is ScriptExecutionType.LOCAL
    assert script.risk_level is ScriptRiskLevel.SAFE
    assert script.requires_confirmation is False
    assert script.version == 1
    assert script.project_id is None


def test_script_normalizes_optional_interpreter() -> None:
    script = make_script(interpreter="  /bin/bash  ")
    blank_interpreter_script = make_script(interpreter="  ")

    assert script.interpreter == "/bin/bash"
    assert blank_interpreter_script.interpreter is None


def test_script_parameters_are_defensively_copied() -> None:
    parameters = {"options": {"recursive": True}}
    expected = deepcopy(parameters)
    script = make_script(parameters=parameters)
    parameters["options"]["recursive"] = False

    assert script.parameters == expected
    returned_parameters = script.parameters
    assert returned_parameters is not None
    returned_parameters["options"]["recursive"] = False

    assert script.parameters == expected


@pytest.mark.parametrize("name", ["", "   ", "x" * 256])
def test_script_rejects_invalid_name(name: str) -> None:
    with pytest.raises(InvalidScript):
        make_script(name=name)


def test_script_rejects_invalid_version_and_confirmation_flag() -> None:
    with pytest.raises(InvalidScript):
        make_script(version=0)
    with pytest.raises(InvalidScript):
        make_script(version=True)
    with pytest.raises(InvalidScript):
        make_script(requires_confirmation=1)


def test_script_rejects_naive_timestamps() -> None:
    created_at = datetime(2026, 1, 1)

    with pytest.raises(InvalidScript):
        make_script(created_at=created_at, updated_at=created_at)


def test_script_rejects_update_or_deletion_out_of_order() -> None:
    created_at = datetime(2026, 1, 2, tzinfo=UTC)

    with pytest.raises(InvalidScript):
        make_script(
            created_at=created_at,
            updated_at=created_at - timedelta(seconds=1),
        )
    with pytest.raises(InvalidScript):
        make_script(
            created_at=created_at,
            updated_at=created_at,
            deleted_at=created_at - timedelta(seconds=1),
        )
