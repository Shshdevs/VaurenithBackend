import pytest

from app.domain.automation.exceptions import InvalidScript
from app.domain.automation.value_objects import ScriptInterpreter, ScriptName


def test_script_name_trims_whitespace_and_compares_by_value() -> None:
    first = ScriptName("  Backup  ")
    second = ScriptName("Backup")

    assert first.value == "Backup"
    assert first == second
    assert hash(first) == hash(second)


@pytest.mark.parametrize("value", ["", "   ", "x" * 256])
def test_script_name_rejects_invalid_values(value: str) -> None:
    with pytest.raises(InvalidScript):
        ScriptName(value)


def test_script_interpreter_trims_whitespace() -> None:
    assert ScriptInterpreter("  bash  ").value == "bash"


@pytest.mark.parametrize("value", ["", "   ", "x" * 101])
def test_script_interpreter_rejects_invalid_values(value: str) -> None:
    with pytest.raises(InvalidScript):
        ScriptInterpreter(value)
