from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.preferences.dto import SettingData
from app.application.preferences.exceptions import (
    ClientDeviceNotFound,
    SettingAlreadyExists,
)
from app.application.preferences.interfaces import SettingRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.preferences import InvalidSetting, Setting, SettingScope
from app.domain.synchronization import ChangeOperation


class CreateSetting:
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
    async def create_setting(
        self,
        identity: VerifiedIdentity,
        scope: SettingScope,
        key: str,
        value: Any | None,
        client_device_id: UUID | None,
    ) -> SettingData:
        try:
            scope = SettingScope(scope)
            now = datetime.now(UTC)
            setting = Setting(
                uuid4(), identity.user_id, scope, key, now, now, client_device_id, value
            )
        except (InvalidSetting, ValueError) as error:
            raise InvalidInput(str(error)) from error
        if client_device_id and not await self._repository.owns_client_device(
            identity.user_id, client_device_id
        ):
            raise ClientDeviceNotFound(str(client_device_id))
        if not await self._repository.create(setting):
            raise SettingAlreadyExists()
        await self._recorder.execute(
            identity,
            EntityType.SETTINGS,
            setting.id,
            ChangeOperation.INSERT,
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
