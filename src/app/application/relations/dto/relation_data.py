from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from app.domain.common.enums import EntityType, RelationOrigin, RelationType
from app.domain.relations import Relation


@dataclass(frozen=True)
class RelationData:
    id: UUID
    project_id: UUID
    source_entity_type: EntityType
    source_entity_id: UUID
    target_entity_type: EntityType
    target_entity_id: UUID
    relation_type: RelationType
    origin: RelationOrigin
    confidence: Decimal | None
    metadata: Any | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_relation(cls, relation: Relation) -> RelationData:
        return cls(
            id=relation.id,
            project_id=relation.project_id,
            source_entity_type=relation.source_entity_type,
            source_entity_id=relation.source_entity_id,
            target_entity_type=relation.target_entity_type,
            target_entity_id=relation.target_entity_id,
            relation_type=relation.relation_type,
            origin=relation.origin,
            confidence=relation.confidence,
            metadata=relation.metadata,
            created_at=relation.created_at,
            updated_at=relation.updated_at,
        )
