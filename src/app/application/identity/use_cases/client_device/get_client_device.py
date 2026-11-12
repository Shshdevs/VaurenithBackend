from uuid import UUID

from app.application.identity.dto import ClientDeviceData, VerifiedIdentity
from app.application.identity.exceptions import ClientDeviceNotFound
from app.application.identity.interfaces import ClientDeviceRepository


class GetClientDevice:
    def __init__(self, repository: ClientDeviceRepository) -> None:
        self._repository = repository

    async def execute(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> ClientDeviceData:
        device = await self._repository.get_owned(identity.user_id, device_id)
        if device is None:
            raise ClientDeviceNotFound()
        return ClientDeviceData.from_entity(device)
