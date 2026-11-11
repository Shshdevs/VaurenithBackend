from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.api.schemas.common import Schema
from app.domain.preferences import SettingScope


class SettingData(Schema):
    id: UUID
    user_id: UUID
    client_device_id: UUID | None
    scope: SettingScope
    key: str
    value: Any | None
    version: int
    created_at: datetime
    updated_at: datetime


class SettingCreateRequest(Schema):
    scope: SettingScope
    key: str
    value: Any | None = None
    client_device_id: UUID | None = None


class SettingUpdateRequest(Schema):
    expected_version: int = Field(ge=1, le=2**63 - 2)
    value: Any | None
