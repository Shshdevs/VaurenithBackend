from copy import deepcopy
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import uuid4

import pytest

from app.domain.common.enums import RelationOrigin
from app.domain.development.entities.dependency import Dependency
from app.domain.development.enums import DependencyType
from app.domain.development.exceptions import InvalidDependency


def make_dependency(**overrides: Any) -> Dependency:
    values: dict[str, Any] = {
        "entity_id": uuid4(),
        "source_component_id": uuid4(),
        "target_component_id": uuid4(),
        "dependency_type": DependencyType.CALL,
        "confidence": Decimal("0.8765"),
        "analyzed_at": datetime(2026, 1, 1, tzinfo=UTC),
    }
    values.update(overrides)
    return Dependency(**values)


def test_dependency_exposes_values_and_defaults() -> None:
    dependency = make_dependency()

    assert dependency.dependency_type is DependencyType.CALL
    assert dependency.is_directed is True
    assert dependency.source_type is RelationOrigin.AUTOMATIC
    assert dependency.confidence == Decimal("0.8765")
    assert dependency.confidence_value is not None
    assert dependency.confidence_value.value == Decimal("0.8765")


@pytest.mark.parametrize("confidence", [Decimal("-0.0001"), Decimal("1.0001")])
def test_dependency_rejects_confidence_outside_unit_interval(
    confidence: Decimal,
) -> None:
    with pytest.raises(InvalidDependency):
        make_dependency(confidence=confidence)


def test_dependency_rejects_confidence_that_requires_rounding() -> None:
    with pytest.raises(InvalidDependency):
        make_dependency(confidence=Decimal("0.12345"))


def test_dependency_normalizes_confidence_to_four_decimal_places() -> None:
    dependency = make_dependency(confidence=Decimal("0.50000"))

    assert dependency.confidence == Decimal("0.5000")


def test_dependency_rejects_non_finite_confidence() -> None:
    with pytest.raises(InvalidDependency):
        make_dependency(confidence=Decimal("NaN"))


def test_dependency_metadata_is_defensively_copied() -> None:
    metadata = {"analysis": {"version": 1}}
    expected = deepcopy(metadata)
    dependency = make_dependency(metadata=metadata)
    metadata["analysis"]["version"] = 2

    assert dependency.metadata == expected
    returned_metadata = dependency.metadata
    assert returned_metadata is not None
    returned_metadata["analysis"]["version"] = 3
    assert dependency.metadata == expected


def test_dependency_rejects_naive_analysis_timestamp() -> None:
    with pytest.raises(InvalidDependency):
        make_dependency(analyzed_at=datetime(2026, 1, 1))
