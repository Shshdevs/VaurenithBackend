from typing import Any
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class NoOpRecordChange:
    async def execute(
        self,
        identity: VerifiedIdentity,
        entity_type: EntityType,
        entity_id: UUID,
        operation: ChangeOperation,
        version: int,
        payload: Any | None = None,
    ) -> None:
        return None
