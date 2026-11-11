from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.preferences.exceptions import (
    SettingNotFound,
    SettingVersionConflict,
)
from app.application.preferences.interfaces import SettingRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.synchronization import ChangeOperation


class DeleteSetting:
    def __init__(
        self,
        repository: SettingRepository,
        recorder: ChangeRecorder,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._repository = repository
        self._recorder = recorder
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(
        self, identity: VerifiedIdentity, setting_id: UUID, expected_version: int
    ) -> None:
        existing = await self._repository.get_by_id(identity.user_id, setting_id)
        if existing is None:
            raise SettingNotFound(str(setting_id))
        if existing.version != expected_version:
            raise SettingVersionConflict(expected_version, existing.version)
        if not await self._repository.delete(
            identity.user_id, setting_id, expected_version
        ):
            raise SettingVersionConflict(expected_version)
        await self._recorder.execute(
            identity,
            EntityType.SETTINGS,
            existing.id,
            ChangeOperation.DELETE,
            expected_version + 1,
            {
                "scope": existing.scope.value,
                "key": existing.key,
                "client_device_id": str(existing.client_device_id)
                if existing.client_device_id
                else None,
            },
        )
