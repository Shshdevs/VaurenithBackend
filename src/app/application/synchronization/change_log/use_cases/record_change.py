from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.application.identity import VerifiedIdentity
from app.application.synchronization.change_log.interfaces import ChangeLogRepository
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeLog, ChangeOperation


class RecordChange:
    def __init__(self, repository: ChangeLogRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        entity_type: EntityType,
        entity_id: UUID,
        operation: ChangeOperation,
        version: int,
        payload: Any | None = None,
    ) -> None:
        event = ChangeLog(
            change_log_id=uuid4(),
            user_id=identity.user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            operation=operation,
            version=version,
            changed_by_user_id=identity.user_id,
            created_at=datetime.now(UTC),
            payload=payload,
        )
        await self._repository.create(event)
