from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DatabaseData
from app.application.infrastructure.exceptions import DatabaseNotFound
from app.application.infrastructure.interfaces import DatabaseRepository


class GetDatabase:
    def __init__(self, database_repository: DatabaseRepository) -> None:
        self._database_repository = database_repository

    async def execute(self, identity: VerifiedIdentity, database_id: UUID) -> DatabaseData:
        database = await self._database_repository.get_by_id(identity, database_id)
        if database is None:
            raise DatabaseNotFound(str(database_id))
        return DatabaseData.from_database(database)
