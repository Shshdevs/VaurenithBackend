from app.application.identity import VerifiedIdentity
from app.application.synchronization.dto import ChangeLogData
from app.application.synchronization.interfaces import ChangeLogRepository


class GetUserChangeLog:
    def __init__(self, repository: ChangeLogRepository) -> None:
        self._repository = repository

    async def execute(
        self, identity: VerifiedIdentity, after_sequence: int = 0, limit: int = 100
    ) -> list[ChangeLogData]:
        changes = await self._repository.get_by_user(
            identity.user_id, after_sequence=after_sequence, limit=limit
        )
        return [ChangeLogData.from_change_log(change) for change in changes]
