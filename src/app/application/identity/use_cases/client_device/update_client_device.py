from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity.dto import ClientDeviceData, VerifiedIdentity
from app.application.identity.exceptions import ClientDeviceNotFound
from app.application.identity.interfaces import ClientDeviceRepository


class UpdateClientDevice:
    def __init__(
        self, repository: ClientDeviceRepository, unit_of_work: UnitOfWork
    ) -> None:
        self._repository = repository
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(
        self,
        identity: VerifiedIdentity,
        device_id: UUID,
        name: str | None,
        app_version: str | None,
        app_version_provided: bool,
    ) -> ClientDeviceData:
        if name is None and not app_version_provided:
            raise InvalidInput("At least one device metadata field must be provided")
        device = await self._repository.get_owned(
            identity.user_id, device_id, for_update=True
        )
        if device is None:
            raise ClientDeviceNotFound()
        device.update_metadata(name, app_version, app_version_provided)
        await self._repository.save(device)
        return ClientDeviceData.from_entity(device)
