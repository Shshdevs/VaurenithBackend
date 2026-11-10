from typing import Any, Protocol
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class ChangeRecorder(Protocol):
    async def execute(
        self,
        identity: VerifiedIdentity,
        entity_type: EntityType,
        entity_id: UUID,
        operation: ChangeOperation,
        version: int,
        payload: Any | None = None,
    ) -> None: ...
