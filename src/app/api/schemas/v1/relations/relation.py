from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.common.enums import EntityType, RelationOrigin, RelationType


class RelationData(Schema):
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


class RelationCreateRequest(Schema):
    source_entity_type: EntityType
    source_entity_id: UUID
    target_entity_type: EntityType
    target_entity_id: UUID
    relation_type: RelationType
    confidence: Decimal | None = Field(
        default=None, ge=0, le=1, max_digits=5, decimal_places=4
    )
    metadata: dict[str, Any] | None = None


class RelationUpdateRequest(RelationCreateRequest):
    pass
