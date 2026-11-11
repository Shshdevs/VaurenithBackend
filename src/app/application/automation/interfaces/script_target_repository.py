from typing import Protocol
from uuid import UUID

from app.domain.automation import ScriptTarget


class ScriptTargetRepository(Protocol):
    async def get_targets(self, user_id: UUID, script_id: UUID) -> list[ScriptTarget]: ...
    async def create_target(self, user_id: UUID, target: ScriptTarget) -> None: ...
    async def delete_target(
        self, user_id: UUID, script_id: UUID, target_id: UUID
    ) -> bool: ...
