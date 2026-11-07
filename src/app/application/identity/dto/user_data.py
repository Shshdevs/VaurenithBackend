from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class UserData:
    id: UUID
    email: str
    display_name: str | None
    nickname: str
    auth_provider: str | None
    created_at: datetime
    updated_at: datetime
