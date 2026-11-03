from copy import deepcopy
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from app.domain.common.enums import EntityType, RelationOrigin, RelationType
from app.domain.relations.entities.relations import Relation
from app.domain.relations.exceptions import InvalidRelation


def make_relation(**overrides: Any) -> Relation:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "project_id": uuid4(),
        "source_entity_type": EntityType.REPOSITORY,
        "source_entity_id": uuid4(),
        "target_entity_type": EntityType.CODE_COMPONENT,
        "target_entity_id": uuid4(),
        "relation_type": RelationType.CONTAINS,
        "origin": RelationOrigin.AUTOMATIC,
        "created_at": created_at,
        "updated_at": created_at,
    }
    values.update(overrides)
    return Relation(**values)


def test_relation_exposes_fields_and_entity_references() -> None:
    source_id = uuid4()
    target_id = uuid4()
    relation = make_relation(
        source_entity_id=source_id,
        target_entity_id=target_id,
        confidence=Decimal("0.8750"),
    )

    assert relation.source_entity_type is EntityType.REPOSITORY
    assert relation.source_entity_id == source_id
    assert relation.source_reference.entity_type is EntityType.REPOSITORY
    assert relation.source_reference.entity_id == source_id
    assert relation.target_entity_type is EntityType.CODE_COMPONENT
    assert relation.target_entity_id == target_id
    assert relation.target_reference.entity_id == target_id
    assert relation.relation_type is RelationType.CONTAINS
    assert relation.origin is RelationOrigin.AUTOMATIC
    assert relation.confidence == Decimal("0.8750")


def test_relation_metadata_is_defensively_copied() -> None:
    metadata = {"details": {"source": "scanner"}}
    expected = deepcopy(metadata)
    relation = make_relation(metadata=metadata)
    metadata["details"]["source"] = "changed"

    assert relation.metadata == expected
    returned_metadata = relation.metadata
    assert returned_metadata is not None
    returned_metadata["details"]["source"] = "changed again"

    assert relation.metadata == expected


@pytest.mark.parametrize("confidence", [Decimal("-0.0001"), Decimal("1.0001")])
def test_relation_rejects_confidence_outside_range(confidence: Decimal) -> None:
    with pytest.raises(InvalidRelation):
        make_relation(confidence=confidence)


def test_relation_rejects_confidence_that_requires_rounding() -> None:
    with pytest.raises(InvalidRelation):
        make_relation(confidence=Decimal("0.12345"))


def test_relation_rejects_naive_timestamps() -> None:
    created_at = datetime(2026, 1, 1)

    with pytest.raises(InvalidRelation):
        make_relation(created_at=created_at, updated_at=created_at)


def test_relation_rejects_update_before_creation() -> None:
    created_at = datetime(2026, 1, 2, tzinfo=UTC)

    with pytest.raises(InvalidRelation):
        make_relation(
            created_at=created_at,
            updated_at=created_at - timedelta(seconds=1),
        )


def test_relation_rejects_invalid_enum_and_identifier_values() -> None:
    with pytest.raises(InvalidRelation):
        make_relation(source_entity_id="invalid")
    with pytest.raises(InvalidRelation):
        make_relation(relation_type="contains")
