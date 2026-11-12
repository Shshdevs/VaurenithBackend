from app.application.identity.dto import ClientDeviceData, VerifiedIdentity
from app.application.identity.interfaces import ClientDeviceRepository


class ListClientDevices:
    def __init__(self, repository: ClientDeviceRepository) -> None:
        self._repository = repository

    async def execute(self, identity: VerifiedIdentity) -> list[ClientDeviceData]:
        devices = await self._repository.list_by_user(identity.user_id)
        return [ClientDeviceData.from_entity(device) for device in devices]
