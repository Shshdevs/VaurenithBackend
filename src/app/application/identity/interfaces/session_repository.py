from datetime import datetime
from typing import Protocol

from app.domain.identity import TokenHash


class SessionRepository(Protocol):
    async def has_active_session(
        self,
        token_hash: TokenHash,
        at: datetime,
    ) -> bool: ...

    async def revoke_session(
        self,
        token_hash: TokenHash,
        at: datetime,
    ) -> bool: ...
