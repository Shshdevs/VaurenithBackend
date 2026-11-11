from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpRecordChange, NoOpUnitOfWork

from app.application.identity import VerifiedIdentity
from app.application.preferences.exceptions import ClientDeviceNotFound
from app.application.preferences.use_cases.settings import (
    CreateSetting,
    GetSettings,
    UpdateSetting,
)
from app.domain.identity import EmailAddress, TokenHash
from app.domain.preferences import Setting, SettingScope


class SettingRepositoryStub:
    def __init__(self) -> None:
        self.settings: dict[UUID, Setting] = {}
        self.device_owner: tuple[UUID, UUID] | None = None

    async def get_by_id(self, user_id: UUID, setting_id: UUID) -> Setting | None:
        setting = self.settings.get(setting_id)
        return setting if setting is not None and setting.user_id == user_id else None

    async def get_for_scope(
        self, user_id: UUID, scope: SettingScope, client_device_id: UUID | None
    ) -> list[Setting]:
        return [
            setting
            for setting in self.settings.values()
            if setting.user_id == user_id
            and setting.scope is scope
            and setting.client_device_id == client_device_id
        ]

    async def owns_client_device(self, user_id: UUID, client_device_id: UUID) -> bool:
        return self.device_owner == (user_id, client_device_id)

    async def create(self, setting: Setting) -> bool:
        if any(
            item.user_id == setting.user_id
            and item.scope is setting.scope
            and item.client_device_id == setting.client_device_id
            and item.key == setting.key
            for item in self.settings.values()
        ):
            return False
        self.settings[setting.id] = setting
        return True

    async def update(self, setting: Setting, expected_version: int) -> bool:
        existing = self.settings.get(setting.id)
        if existing is None or existing.version != expected_version:
            return False
        self.settings[setting.id] = setting
        return True

    async def delete(self, user_id: UUID, setting_id: UUID, expected_version: int) -> bool:
        setting = await self.get_by_id(user_id, setting_id)
        if setting is None or setting.version != expected_version:
            return False
        del self.settings[setting_id]
        return True


def make_identity() -> VerifiedIdentity:
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="preferences-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


@pytest.mark.anyio
async def test_create_and_update_setting_increments_version() -> None:
    identity = make_identity()
    repository = SettingRepositoryStub()
    recorder = NoOpRecordChange()
    unit_of_work = NoOpUnitOfWork()
    create = CreateSetting(repository, recorder, unit_of_work)
    update = UpdateSetting(repository, recorder, unit_of_work)

    created = await create.create_setting(
        identity, SettingScope.GLOBAL, "theme", {"mode": "dark"}, None
    )
    updated = await update.update_setting(identity, created.id, 1, {"mode": "light"})

    assert created.version == 1
    assert updated.version == 2
    assert updated.value == {"mode": "light"}
    assert updated.user_id == identity.user_id


@pytest.mark.anyio
async def test_client_settings_require_owned_device() -> None:
    identity = make_identity()
    repository = SettingRepositoryStub()
    use_case = GetSettings(repository)

    with pytest.raises(ClientDeviceNotFound):
        await use_case.execute(identity, SettingScope.CLIENT, uuid4())
