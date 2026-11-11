from datetime import datetime
from uuid import UUID

from app.api.schemas.common import Schema
from app.domain.infrastructure.enums import AuthenticationType, ConnectionStatus


class ConnectionData(Schema):
    id: UUID
    device_id: UUID
    name: str
    slug: str
    host: str
    port: int
    username: str
    authentication_type: AuthenticationType
    connection_timeout: int
    is_default: bool
    last_connected_at: datetime | None
    last_status: ConnectionStatus
    version: int
    created_at: datetime
    updated_at: datetime
