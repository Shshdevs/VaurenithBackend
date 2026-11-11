from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from app.domain.infrastructure import Connection


@dataclass(frozen=True)
class ConnectionData:
    id: UUID
    device_id: UUID
    name: str
    slug: str
    host: str
    port: int
    username: str
    authentication_type: str
    connection_timeout: int
    is_default: bool
    last_connected_at: datetime | None
    last_status: str
    version: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_connection(cls, connection: Connection) -> ConnectionData:
        return cls(
            id=connection.id,
            device_id=connection.device_id,
            name=connection.name,
            slug=connection.slug,
            host=connection.host,
            port=connection.port,
            username=connection.username,
            authentication_type=connection.authentication_type.value,
            connection_timeout=connection.connection_timeout,
            is_default=connection.is_default,
            last_connected_at=connection.last_connected_at,
            last_status=connection.last_status.value,
            version=connection.version,
            created_at=connection.created_at,
            updated_at=connection.updated_at,
        )
