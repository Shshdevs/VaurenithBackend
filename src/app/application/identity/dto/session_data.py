from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.identity import Session


@dataclass(frozen=True, slots=True)
class SessionData:
    id: UUID
    client_device_id: UUID
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None

    @classmethod
    def from_entity(cls, session: Session) -> SessionData:
        return cls(
            id=session.id,
            client_device_id=session.client_device_id,
            created_at=session.created_at,
            expires_at=session.expires_at,
            revoked_at=session.revoked_at,
        )
