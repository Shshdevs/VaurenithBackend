from datetime import datetime

from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.infrastructure.enums import ConnectionStatus


class ConnectionStatusUpdateRequest(Schema):
    version: int = Field(ge=1)
    status: ConnectionStatus
    last_connected_at: datetime | None = None
    last_error: str | None = Field(default=None, max_length=4000)
