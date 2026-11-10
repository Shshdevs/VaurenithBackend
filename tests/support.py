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


class NoOpUnitOfWork:
    async def __aenter__(self) -> None:
        return None

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        return None

    def transaction(self) -> "NoOpUnitOfWork":
        return self
