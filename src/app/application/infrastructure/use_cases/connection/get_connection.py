from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ConnectionData
from app.application.infrastructure.exceptions import ConnectionNotFound
from app.application.infrastructure.interfaces import ConnectionRepository


class GetConnection:
    def __init__(self, connection_repository: ConnectionRepository) -> None:
        self._connection_repository = connection_repository

    async def execute(
        self, identity: VerifiedIdentity, connection_id: UUID
    ) -> ConnectionData:
        connection = await self._connection_repository.get_by_id(identity, connection_id)
        if connection is None:
            raise ConnectionNotFound(str(connection_id))
        return ConnectionData.from_connection(connection)
