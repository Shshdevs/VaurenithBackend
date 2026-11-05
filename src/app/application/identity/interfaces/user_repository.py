from typing import Protocol
from uuid import UUID

from ....domain.identity import Session, User


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UUID) -> User | None: ...

    async def register(self, user: User, session: Session) -> None: ...
