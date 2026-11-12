from uuid import UUID

from app.application.identity.dto import SessionData, VerifiedIdentity
from app.application.identity.exceptions import ClientDeviceNotFound
from app.application.identity.interfaces import (
    ClientDeviceRepository,
    SessionRepository,
)


class ListDeviceSessions:
    def __init__(
        self,
        client_device_repository: ClientDeviceRepository,
        session_repository: SessionRepository,
    ) -> None:
        self._client_device_repository = client_device_repository
        self._session_repository = session_repository

    async def execute(
        self, identity: VerifiedIdentity, device_id: UUID
    ) -> list[SessionData]:
        device = await self._client_device_repository.get_owned(identity.user_id, device_id)
        if device is None:
            raise ClientDeviceNotFound()
        sessions = await self._session_repository.list_device_sessions(
            identity.user_id, device_id
        )
        return [SessionData.from_entity(session) for session in sessions]
