from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeLog, ChangeOperation, InvalidChangeLog


def make_change_log(**overrides: object) -> ChangeLog:
    values: dict[str, object] = {
        "change_log_id": uuid4(),
        "user_id": uuid4(),
        "entity_type": EntityType.PROJECT,
        "entity_id": uuid4(),
        "operation": ChangeOperation.UPDATE,
        "version": 1,
        "changed_by_user_id": uuid4(),
        "created_at": datetime(2025, 1, 1, tzinfo=UTC),
        "payload": {"name": "sample"},
    }
    values.update(overrides)
    return ChangeLog(**values)  # type: ignore[arg-type]


def test_change_log_exposes_fields_and_copies_payload() -> None:
    payload = {"items": [1]}
    change_log = make_change_log(payload=payload)
    payload["items"].append(2)

    assert change_log.entity_type is EntityType.PROJECT
    assert change_log.operation is ChangeOperation.UPDATE
    assert change_log.version == 1
    assert change_log.payload == {"items": [1]}
    returned = change_log.payload
    assert returned is not None
    returned["items"].append(3)
    assert change_log.payload == {"items": [1]}


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("change_log_id", "invalid"),
        ("user_id", "invalid"),
        ("entity_type", "project"),
        ("entity_id", "invalid"),
        ("operation", "update"),
        ("version", 0),
        ("version", 2**63),
        ("version", True),
        ("changed_by_user_id", "invalid"),
        ("changed_by_client_id", "invalid"),
        ("created_at", datetime(2025, 1, 1)),
    ],
)
def test_change_log_rejects_invalid_fields(field: str, value: object) -> None:
    with pytest.raises(InvalidChangeLog):
        make_change_log(**{field: value})


def test_change_log_allows_optional_client_and_payload() -> None:
    change_log = make_change_log(changed_by_client_id=None, payload=None)

    assert change_log.changed_by_client_id is None
    assert change_log.payload is None
