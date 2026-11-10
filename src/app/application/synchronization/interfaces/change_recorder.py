from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol
from uuid import UUID

from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation

if TYPE_CHECKING:
    from app.application.identity.dto import VerifiedIdentity


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
