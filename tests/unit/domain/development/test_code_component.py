from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest

from app.domain.development.entities.code_component import CodeComponent
from app.domain.development.enums import ComponentType
from app.domain.development.exceptions import InvalidCodeComponent, InvalidCommitHash


def make_component(**overrides: Any) -> CodeComponent:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "repository_id": uuid4(),
        "name": "  lookup_user  ",
        "path": "src/users.py",
        "component_type": ComponentType.FUNCTION,
        "created_at": created_at,
        "updated_at": created_at,
    }
    values.update(overrides)
    return CodeComponent(**values)


def test_component_normalizes_name_and_optional_text() -> None:
    component = make_component(language=" Python ", symbol="  lookup_user  ")

    assert component.name == "lookup_user"
    assert component.path == "src/users.py"
    assert component.language == "Python"
    assert component.symbol == "lookup_user"
    assert component.component_type is ComponentType.FUNCTION


def test_component_rejects_self_parent() -> None:
    entity_id = uuid4()

    with pytest.raises(InvalidCodeComponent):
        make_component(entity_id=entity_id, parent_id=entity_id)


@pytest.mark.parametrize(
    ("start_line", "end_line"),
    [(0, 1), (1, 0), (5, 4), (True, 2)],
)
def test_component_rejects_invalid_line_ranges(start_line: int, end_line: int) -> None:
    with pytest.raises(InvalidCodeComponent):
        make_component(start_line=start_line, end_line=end_line)


def test_component_rejects_invalid_source_commit_hash() -> None:
    with pytest.raises(InvalidCommitHash):
        make_component(source_commit_hash="not-a-hash")


def test_component_rejects_naive_timestamps() -> None:
    created_at = datetime(2026, 1, 1)

    with pytest.raises(InvalidCodeComponent):
        make_component(created_at=created_at, updated_at=created_at)


def test_component_rejects_update_before_creation() -> None:
    created_at = datetime(2026, 1, 2, tzinfo=UTC)

    with pytest.raises(InvalidCodeComponent):
        make_component(
            created_at=created_at,
            updated_at=created_at - timedelta(seconds=1),
        )
