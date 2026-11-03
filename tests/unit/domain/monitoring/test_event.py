from copy import deepcopy
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.domain.common.enums import EntityType
from app.domain.monitoring.entities.event import Event
from app.domain.monitoring.enums import EventResult, EventType
from app.domain.monitoring.exceptions import InvalidEvent


def make_event(**overrides: Any) -> Event:
    values: dict[str, Any] = {
        "event_id": uuid4(),
        "user_id": uuid4(),
        "event_type": EventType.DEVICE_ADDED,
        "result": EventResult.SUCCESS,
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return Event(**values)


def test_event_exposes_primary_and_referenced_entity_ids() -> None:
    event_id = uuid4()
    related_entity_id = uuid4()
    event = make_event(
        event_id=event_id,
        entity_type=EntityType.DEVICE,
        entity_id=related_entity_id,
    )

    assert event.id == event_id
    assert event.entity_type is EntityType.DEVICE
    assert event.entity_id == related_entity_id
    assert event.event_type is EventType.DEVICE_ADDED
    assert event.result is EventResult.SUCCESS


def test_event_metadata_is_defensively_copied() -> None:
    metadata = {"details": {"source": "agent"}}
    expected = deepcopy(metadata)
    event = make_event(metadata=metadata)
    metadata["details"]["source"] = "changed"

    assert event.metadata == expected
    returned_metadata = event.metadata
    assert returned_metadata is not None
    returned_metadata["details"]["source"] = "changed again"

    assert event.metadata == expected


def test_event_rejects_invalid_event_type_and_uuid() -> None:
    with pytest.raises(InvalidEvent):
        make_event(event_type="device_added")
    with pytest.raises(InvalidEvent):
        make_event(project_id="invalid")


def test_event_rejects_naive_creation_time() -> None:
    with pytest.raises(InvalidEvent):
        make_event(created_at=datetime(2026, 1, 1))
