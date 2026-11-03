from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import pytest

from app.domain.monitoring.entities.log_metadata import LogMetadata
from app.domain.monitoring.exceptions import InvalidLogMetadata


def make_log_metadata(**overrides: Any) -> LogMetadata:
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "user_id": uuid4(),
        "source": "  cloudwatch  ",
        "created_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return LogMetadata(**values)


def test_log_metadata_exposes_table_fields() -> None:
    project_id = uuid4()
    collected_at = datetime(2026, 1, 2, tzinfo=UTC)
    log_metadata = make_log_metadata(
        project_id=project_id,
        severity="error",
        records_count=42,
        collected_at=collected_at,
    )

    assert log_metadata.source == "  cloudwatch  "
    assert log_metadata.project_id == project_id
    assert log_metadata.severity == "error"
    assert log_metadata.records_count == 42
    assert log_metadata.collected_at == collected_at


def test_log_metadata_rejects_values_outside_column_limits() -> None:
    with pytest.raises(InvalidLogMetadata):
        make_log_metadata(source="x" * 256)
    with pytest.raises(InvalidLogMetadata):
        make_log_metadata(severity="x" * 51)
    with pytest.raises(InvalidLogMetadata):
        make_log_metadata(records_count=2**63)


def test_log_metadata_rejects_invalid_identifier_and_naive_timestamps() -> None:
    with pytest.raises(InvalidLogMetadata):
        make_log_metadata(container_id="invalid")
    with pytest.raises(InvalidLogMetadata):
        make_log_metadata(collected_at=datetime(2026, 1, 1))
