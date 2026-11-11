from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.preferences.dto import SettingData
from app.application.preferences.exceptions import (
    SettingNotFound,
    SettingVersionConflict,
)
from app.application.preferences.interfaces import SettingRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.preferences import InvalidSetting, Setting
from app.domain.synchronization import ChangeOperation


class UpdateSetting:
    def __init__(
        self,
        repository: SettingRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository, self._recorder, self._unit_of_work = (
            repository,
            recorder,
            unit_of_work,
        )

    @transactional
    async def update_setting(
        self,
        identity: VerifiedIdentity,
        setting_id: UUID,
        expected_version: int,
        value: Any | None,
    ) -> SettingData:
        existing = await self._repository.get_by_id(identity.user_id, setting_id)
        if existing is None:
            raise SettingNotFound(str(setting_id))
        if existing.version != expected_version:
            raise SettingVersionConflict(expected_version, existing.version)
        try:
            setting = Setting(
                existing.id,
                identity.user_id,
                existing.scope,
                existing.key,
                existing.created_at,
                datetime.now(UTC),
                existing.client_device_id,
                value,
                expected_version + 1,
            )
        except InvalidSetting as error:
            raise InvalidInput(str(error)) from error
        if not await self._repository.update(setting, expected_version):
            raise SettingVersionConflict(expected_version)
        await self._recorder.execute(
            identity,
            EntityType.SETTINGS,
            setting.id,
            ChangeOperation.UPDATE,
            setting.version,
            {
                "scope": setting.scope.value,
                "key": setting.key,
                "client_device_id": str(setting.client_device_id)
                if setting.client_device_id
                else None,
            },
        )
        return SettingData(setting)
