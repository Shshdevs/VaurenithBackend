from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.preferences.dto import SettingData
from app.application.preferences.exceptions import ClientDeviceNotFound
from app.application.preferences.interfaces import SettingRepository
from app.domain.preferences import SettingScope


class GetSettings:
    def __init__(self, repository: SettingRepository) -> None:
        self._repository = repository

    async def execute(
        self,
        identity: VerifiedIdentity,
        scope: SettingScope,
        client_device_id: UUID | None,
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
