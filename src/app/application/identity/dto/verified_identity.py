from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ....domain.identity import EmailAddress, TokenHash


@dataclass(frozen=True, slots=True)
class VerifiedIdentity:
    user_id: UUID
    email: EmailAddress
    auth_provider: str
    expires_at: datetime
    token_hash: TokenHash
