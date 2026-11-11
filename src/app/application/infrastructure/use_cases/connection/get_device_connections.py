from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ConnectionData
from app.application.infrastructure.interfaces import ConnectionRepository


class GetDeviceConnections:
    def __init__(self, connection_repository: ConnectionRepository) -> None:
        self._connection_repository = connection_repository

    async def execute(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[ConnectionData]:
        connections = await self._connection_repository.get_by_device(identity, device_id)
        return [ConnectionData.from_connection(connection) for connection in connections]
