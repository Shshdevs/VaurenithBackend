from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.common.enums import RelationOrigin
from app.domain.development.enums import DependencyType


class DependencyData(Schema):
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


class DependencyCreateRequest(Schema):
    source_component_id: UUID
    target_component_id: UUID
    dependency_type: DependencyType
    is_directed: bool = True
    source_type: RelationOrigin = RelationOrigin.AUTOMATIC
    confidence: Decimal | None = Field(
        default=None, ge=0, le=1, max_digits=5, decimal_places=4
    )
    analysis_version: str | None = Field(default=None, max_length=100)
    analyzed_at: datetime | None = None
    metadata: Any | None = None


class DependencyUpdateRequest(DependencyCreateRequest):
    pass
