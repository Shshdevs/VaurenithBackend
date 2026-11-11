from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ContainerData
from app.application.infrastructure.interfaces import ContainerRepository


class GetEnvironmentContainers:
    def __init__(self, container_repository: ContainerRepository) -> None:
        self._container_repository = container_repository

    async def execute(
        self, identity: VerifiedIdentity, environment_id: UUID
    ) -> list[ContainerData]:
        containers = await self._container_repository.get_by_environment(
            identity=identity, environment_id=environment_id
        )
        return [ContainerData.from_container(container) for container in containers]
