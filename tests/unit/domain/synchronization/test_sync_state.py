from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.common.enums import EntityType
from app.domain.synchronization import InvalidSyncState, SyncState, SyncStatus


def make_sync_state(**overrides: object) -> SyncState:
    values: dict[str, object] = {
        "sync_state_id": uuid4(),
        "user_id": uuid4(),
        "client_device_id": uuid4(),
        "updated_at": datetime(2025, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return SyncState(**values)  # type: ignore[arg-type]


def test_device_cursor_defaults_to_pending() -> None:
    state = make_sync_state()

    assert state.entity_type is None
    assert state.entity_id is None
    assert state.status is SyncStatus.PENDING
    assert state.local_version is None
    assert state.server_version is None


def test_entity_sync_state_accepts_entity_pair_and_versions() -> None:
    entity_id = uuid4()
    state = make_sync_state(
        entity_type=EntityType.PROJECT,
        entity_id=entity_id,
        local_version=2,
        server_version=3,
        status=SyncStatus.SYNCED,
        last_synced_at=datetime(2025, 1, 2, tzinfo=UTC),
        last_error=None,
    )

    assert state.entity_type is EntityType.PROJECT
    assert state.entity_id == entity_id
    assert state.local_version == 2
    assert state.server_version == 3
    assert state.status is SyncStatus.SYNCED


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sync_state_id", "invalid"),
        ("user_id", "invalid"),
        ("client_device_id", "invalid"),
        ("entity_type", "project"),
        ("entity_id", "invalid"),
        ("local_version", -1),
        ("local_version", 2**63),
        ("local_version", True),
        ("server_version", -1),
        ("status", "synced"),
        ("updated_at", datetime(2025, 1, 1)),
        ("last_synced_at", datetime(2025, 1, 1)),
        ("last_error", 4),
    ],
)
def test_sync_state_rejects_invalid_fields(field: str, value: object) -> None:
    with pytest.raises(InvalidSyncState):
        make_sync_state(**{field: value})


@pytest.mark.parametrize(
    ("entity_type", "entity_id"),
    [(EntityType.PROJECT, None), (None, uuid4())],
)
def test_sync_state_requires_entity_fields_together(
    entity_type: EntityType | None,
    entity_id: object | None,
) -> None:
    with pytest.raises(InvalidSyncState):
        make_sync_state(
            entity_type=entity_type,
            entity_id=entity_id,
        )
