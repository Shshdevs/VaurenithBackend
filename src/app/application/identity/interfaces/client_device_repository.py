from typing import Protocol
from uuid import UUID

from app.domain.identity import ClientDevice


class ClientDeviceRepository(Protocol):
    async def create(self, device: ClientDevice) -> None: ...

    async def get_owned(
        self, user_id: UUID, device_id: UUID, for_update: bool = False
    ) -> ClientDevice | None: ...

    async def list_by_user(self, user_id: UUID) -> list[ClientDevice]: ...

    async def save(self, device: ClientDevice) -> None: ...
