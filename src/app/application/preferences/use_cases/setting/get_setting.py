from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.preferences.dto import SettingData
from app.application.preferences.exceptions import SettingNotFound
from app.application.preferences.interfaces import SettingRepository


class GetSetting:
    def __init__(self, repository: SettingRepository) -> None:
        self._repository = repository

    async def execute(self, identity: VerifiedIdentity, setting_id: UUID) -> SettingData:
        setting = await self._repository.get_by_id(identity.user_id, setting_id)
        if setting is None:
            raise SettingNotFound(str(setting_id))
        return SettingData(setting)
