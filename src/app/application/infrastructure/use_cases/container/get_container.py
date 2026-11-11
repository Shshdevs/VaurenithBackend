from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ContainerData
from app.application.infrastructure.exceptions import ContainerNotFound
from app.application.infrastructure.interfaces import ContainerRepository


class GetContainer:
    def __init__(self, container_repository: ContainerRepository) -> None:
        self._container_repository = container_repository

    async def execute(
        self, identity: VerifiedIdentity, container_id: UUID
    ) -> ContainerData | None:
        container = await self._container_repository.get_by_id(
            identity=identity, container_id=container_id
        )

        if container is None:
            raise ContainerNotFound(str(container_id))

        return ContainerData.from_container(container=container)
