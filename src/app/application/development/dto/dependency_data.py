from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.domain.common.enums import RelationOrigin
from app.domain.development.enums import DependencyType


@dataclass(frozen=True, slots=True)
class DependencyData:
    id: UUID
    source_component_id: UUID
    target_component_id: UUID
    dependency_type: DependencyType
    is_directed: bool
    source_type: RelationOrigin
    confidence: Decimal | None
    analysis_version: str | None
    analyzed_at: datetime | None
    metadata: Any | None

    @classmethod
    def from_dependency(cls, dependency) -> "DependencyData":
        return cls(
            id=dependency.id,
            source_component_id=dependency.source_component_id,
            target_component_id=dependency.target_component_id,
            dependency_type=dependency.dependency_type,
            is_directed=dependency.is_directed,
            source_type=dependency.source_type,
            confidence=dependency.confidence,
            analysis_version=dependency.analysis_version,
            analyzed_at=dependency.analyzed_at,
            metadata=dependency.metadata,
        )
