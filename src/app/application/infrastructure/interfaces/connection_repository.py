from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.domain.infrastructure import Connection
from app.domain.infrastructure.enums import ConnectionStatus


class ConnectionRepository(Protocol):
    async def get_by_id(
        self, identity: VerifiedIdentity, connection_id: UUID
    ) -> Connection | None: ...

    async def get_by_user(self, identity: VerifiedIdentity) -> list[Connection]: ...

    async def get_by_device(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[Connection]: ...

    async def create(self, identity: VerifiedIdentity, connection: Connection) -> bool: ...

    async def update(
        self, identity: VerifiedIdentity, connection: Connection, expected_version: int
    ) -> bool: ...

    async def update_status(
        self,
        identity: VerifiedIdentity,
        connection_id: UUID,
        expected_version: int,
        status: ConnectionStatus,
        last_connected_at: datetime | None,
        last_error: str | None,
        updated_at: datetime,
    ) -> bool: ...

    async def delete(self, identity: VerifiedIdentity, connection_id: UUID) -> bool: ...
