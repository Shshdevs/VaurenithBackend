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
    SettingNotFound,
    SettingVersionConflict,
)
from app.application.preferences.interfaces import SettingRepository
from app.application.synchronization.interfaces import ChangeRecorder
from app.domain.common.enums import EntityType
from app.domain.preferences import InvalidSetting, Setting, SettingScope
from app.domain.synchronization import ChangeOperation


class GetSettings:
    def __init__(self, repository: SettingRepository) -> None:
        self._repository = repository

    async def execute(
        self, identity: VerifiedIdentity, scope: SettingScope, client_device_id: UUID | None
    ) -> list[SettingData]:
        try:
            scope = SettingScope(scope)
        except ValueError as error:
            raise InvalidInput("Setting scope is invalid") from error
        if (scope is SettingScope.CLIENT) != (client_device_id is not None):
            raise InvalidInput(
                "Client settings require a client device; global settings do not"
            )
        if client_device_id and not await self._repository.owns_client_device(
            identity.user_id, client_device_id
        ):
            raise ClientDeviceNotFound(str(client_device_id))
        values = await self._repository.get_for_scope(
            identity.user_id, scope, client_device_id
        )
        return [SettingData(item) for item in values]


class GetSetting:
    def __init__(self, repository: SettingRepository) -> None:
        self._repository = repository

    async def execute(self, identity: VerifiedIdentity, setting_id: UUID) -> SettingData:
        setting = await self._repository.get_by_id(identity.user_id, setting_id)
        if setting is None:
            raise SettingNotFound(str(setting_id))
        return SettingData(setting)


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
        await self._record(identity, setting, ChangeOperation.INSERT)
        return SettingData(setting)

    async def _record(
        self, identity: VerifiedIdentity, setting: Setting, operation: ChangeOperation
    ) -> None:
        await self._recorder.execute(
            identity,
            EntityType.SETTINGS,
            setting.id,
            operation,
            setting.version,
            {
                "scope": setting.scope.value,
                "key": setting.key,
                "client_device_id": str(setting.client_device_id)
                if setting.client_device_id
                else None,
            },
        )


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


class DeleteSetting:
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
