from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DefaultConnectionConflict
from app.domain.identity import EmailAddress, TokenHash
from app.domain.infrastructure import Connection
from app.domain.infrastructure.enums import AuthenticationType, ConnectionStatus


def make_connection_identity(user_id: UUID | None = None) -> VerifiedIdentity:
    resolved_user_id = user_id or uuid4()
    return VerifiedIdentity(
        user_id=resolved_user_id,
        email=EmailAddress(f"{resolved_user_id}@example.test"),
        auth_provider="connection-test-provider",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("f" * 64),
    )


def make_connection(
    device_id: UUID,
    *,
    connection_id: UUID | None = None,
    name: str = "Primary SSH",
    version: int = 1,
    now: datetime | None = None,
    is_default: bool = False,
    status: ConnectionStatus = ConnectionStatus.UNKNOWN,
    last_connected_at: datetime | None = None,
    last_error: str | None = None,
) -> Connection:
    timestamp = now or datetime.now(UTC)
    return Connection(
        entity_id=connection_id or uuid4(),
        device_id=device_id,
        name=name,
        host="server.example.test",
        port=22,
        username="admin",
        authentication_type=AuthenticationType.SSH_KEY,
        connection_timeout=30,
        is_default=is_default,
        last_connected_at=last_connected_at,
        last_status=status,
        last_error=last_error,
        version=version,
        created_at=timestamp,
        updated_at=timestamp,
    )


class FakeConnectionRepository:
    def __init__(self, device_owners: dict[UUID, UUID] | None = None) -> None:
        self.connections: dict[UUID, Connection] = {}
        self.device_owners = device_owners or {}

    def _owns(self, identity: VerifiedIdentity, device_id: UUID) -> bool:
        return self.device_owners.get(device_id) == identity.user_id

    async def get_by_id(
        self, identity: VerifiedIdentity, connection_id: UUID
    ) -> Connection | None:
        connection = self.connections.get(connection_id)
        if connection is None or not self._owns(identity, connection.device_id):
            return None
        return connection

    async def get_by_user(self, identity: VerifiedIdentity) -> list[Connection]:
        return [
            connection
            for connection in self.connections.values()
            if self._owns(identity, connection.device_id)
        ]

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[Connection]:
        if not self._owns(identity, device_id):
            return []
        return [
            connection
            for connection in self.connections.values()
            if connection.device_id == device_id
        ]

    async def create(self, identity: VerifiedIdentity, connection: Connection) -> bool:
        if not self._owns(identity, connection.device_id):
            return False
        if connection.is_default and any(
            item.device_id == connection.device_id and item.is_default
            for item in self.connections.values()
        ):
            raise DefaultConnectionConflict()
        self.connections[connection.id] = connection
        return True

    async def update(
        self, identity: VerifiedIdentity, connection: Connection, expected_version: int
    ) -> bool:
        existing = await self.get_by_id(identity, connection.id)
        if existing is None or existing.version != expected_version:
            return False
        if connection.is_default and any(
            item.device_id == connection.device_id
            and item.id != connection.id
            and item.is_default
            for item in self.connections.values()
        ):
            raise DefaultConnectionConflict()
        self.connections[connection.id] = connection
        return True

    async def update_status(
        self,
        identity: VerifiedIdentity,
        connection_id: UUID,
        expected_version: int,
        status: ConnectionStatus,
        last_connected_at: datetime | None,
        last_error: str | None,
        updated_at: datetime,
    ) -> bool:
        existing = await self.get_by_id(identity, connection_id)
        if existing is None or existing.version != expected_version:
            return False
        self.connections[connection_id] = Connection(
            entity_id=existing.id,
            device_id=existing.device_id,
            name=existing.name,
            host=existing.host,
            username=existing.username,
            authentication_type=existing.authentication_type,
            created_at=existing.created_at,
            updated_at=updated_at,
            port=existing.port,
            connection_timeout=existing.connection_timeout,
            is_default=existing.is_default,
            last_connected_at=last_connected_at,
            last_status=status,
            last_error=last_error,
            version=expected_version + 1,
        )
        return True

    async def delete(self, identity: VerifiedIdentity, connection_id: UUID) -> bool:
        if await self.get_by_id(identity, connection_id) is None:
            return False
        del self.connections[connection_id]
        return True
