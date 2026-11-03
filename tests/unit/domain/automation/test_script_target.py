from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.domain.automation.entities.script_target import ScriptTarget
from app.domain.automation.exceptions import InvalidScriptTarget


def make_target(**overrides: Any) -> ScriptTarget:
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "script_id": uuid4(),
        "device_id": uuid4(),
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return ScriptTarget(**values)


def test_script_target_exposes_ids_and_created_time() -> None:
    target = make_target()

    assert target.script_id is not None
    assert target.device_id is not None
    assert target.environment_id is None
    assert target.created_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_script_target_accepts_environment_id() -> None:
    environment_id = uuid4()

    assert make_target(environment_id=environment_id).environment_id == environment_id


def test_script_target_rejects_invalid_identifier() -> None:
    with pytest.raises(InvalidScriptTarget):
        make_target(environment_id="invalid")


def test_script_target_rejects_naive_creation_time() -> None:
    with pytest.raises(InvalidScriptTarget):
        make_target(created_at=datetime(2026, 1, 1))
