from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.infrastructure.dto import ContainerData
from app.application.infrastructure.interfaces import ContainerRepository


class GetContainersByProject:
    def __init__(self, container_repository: ContainerRepository) -> None:
        self._container_repository = container_repository

    async def execute(
        self, identity: VerifiedIdentity, project_id: UUID
    ) -> list[ContainerData]:
        containers = await self._container_repository.get_by_project(
            identity=identity, project_id=project_id
        )
        return [ContainerData.from_container(container) for container in containers]
