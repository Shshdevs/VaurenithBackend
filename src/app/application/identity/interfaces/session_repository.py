from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.identity import Session, TokenHash


class SessionRepository(Protocol):
    async def has_active_session(
        self,
        user_id: UUID,
        token_hash: TokenHash,
        at: datetime,
    ) -> bool: ...

    async def has_token_hash(self, token_hash: TokenHash) -> bool: ...

    async def create(self, session: Session) -> None: ...

    async def revoke_device_sessions(
        self,
        user_id: UUID,
        client_device_id: UUID,
        at: datetime,
    ) -> int: ...

    async def list_device_sessions(
        self,
        user_id: UUID,
        client_device_id: UUID,
    ) -> list[Session]: ...

    async def revoke_session(
        self,
        token_hash: TokenHash,
        at: datetime,
    ) -> bool: ...
