from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class IdentityTokenClaims:
    user_id: UUID
    email: str
    auth_provider: str
    expires_at: datetime
