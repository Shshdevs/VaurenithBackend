from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from app.api.schemas.common import Schema
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class ChangeLogData(Schema):
    id: UUID
    user_id: UUID
    entity_type: EntityType
    entity_id: UUID
    operation: ChangeOperation
    version: int
    sequence: int
    changed_by_client_id: UUID | None
    changed_by_user_id: UUID
    payload: Any | None
    created_at: datetime


class ChangeLogResyncRequired(Schema):
    resync_required: Literal[True] = True
    restart_sequence: int
