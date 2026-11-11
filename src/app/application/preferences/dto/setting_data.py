from datetime import datetime
from typing import Any
from uuid import UUID

from app.domain.preferences import Setting, SettingScope


class SettingData:
    def __init__(self, setting: Setting) -> None:
        self.id = setting.id
        self.user_id = setting.user_id
        self.client_device_id = setting.client_device_id
        self.scope = setting.scope
        self.key = setting.key
        self.value: Any | None = setting.value
        self.version = setting.version
        self.created_at: datetime = setting.created_at
        self.updated_at: datetime = setting.updated_at

    id: UUID
    user_id: UUID
    client_device_id: UUID | None
    scope: SettingScope
    key: str
    value: Any | None
    version: int
    created_at: datetime
    updated_at: datetime
