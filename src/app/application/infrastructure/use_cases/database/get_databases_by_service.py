from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import DatabaseData
from app.application.infrastructure.interfaces import DatabaseRepository


class GetDatabasesByService:
    def __init__(self, database_repository: DatabaseRepository) -> None:
        self._database_repository = database_repository

    async def execute(
        self, identity: VerifiedIdentity, service_id: UUID
    ) -> list[DatabaseData]:
        databases = await self._database_repository.get_by_service(identity, service_id)
        return [DatabaseData.from_database(database) for database in databases]
