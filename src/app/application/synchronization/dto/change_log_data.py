from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeLog, ChangeOperation


@dataclass(frozen=True)
class ChangeLogData:
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

    @classmethod
    def from_change_log(cls, change: ChangeLog) -> ChangeLogData:
        if change.sequence is None:
            raise ValueError("Persisted change log entry must have a sequence")
        return cls(
            id=change.id,
            user_id=change.user_id,
            entity_type=change.entity_type,
            entity_id=change.entity_id,
            operation=change.operation,
            version=change.version,
            sequence=change.sequence,
            changed_by_client_id=change.changed_by_client_id,
            changed_by_user_id=change.changed_by_user_id,
            payload=change.payload,
            created_at=change.created_at,
        )
