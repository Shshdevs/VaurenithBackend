from decimal import Decimal
from typing import cast
from uuid import uuid4

import pytest

from app.domain.common.enums import EntityType
from app.domain.common.types import EntityId
from app.domain.relations.exceptions import InvalidRelation
from app.domain.relations.value_objects import EntityReference, RelationConfidence


def test_entity_references_compare_by_type_and_id() -> None:
    entity_id = uuid4()
    first = EntityReference(EntityType.DEVICE, entity_id)
    second = EntityReference(EntityType.DEVICE, entity_id)

    assert first == second
    assert hash(first) == hash(second)


def test_entity_reference_rejects_invalid_values() -> None:
    with pytest.raises(InvalidRelation):
        EntityReference(cast(EntityType, "device"), uuid4())
    with pytest.raises(InvalidRelation):
        EntityReference(EntityType.DEVICE, cast(EntityId, "invalid"))


def test_relation_confidence_normalizes_scale() -> None:
    confidence = RelationConfidence(Decimal("0.25000"))

    assert confidence.value == Decimal("0.2500")


@pytest.mark.parametrize("value", [Decimal("-0.0001"), Decimal("1.0001")])
def test_relation_confidence_rejects_values_outside_range(value: Decimal) -> None:
    with pytest.raises(InvalidRelation):
        RelationConfidence(value)


def test_relation_confidence_rejects_non_finite_or_excess_precision() -> None:
    with pytest.raises(InvalidRelation):
        RelationConfidence(Decimal("NaN"))
    with pytest.raises(InvalidRelation):
        RelationConfidence(Decimal("0.12345"))
