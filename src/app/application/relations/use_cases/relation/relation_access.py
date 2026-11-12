from uuid import UUID

from app.application.relations.exceptions import (
    RelationProjectNotFound,
    RelationReferenceNotFound,
)
from app.application.relations.interfaces import RelationRepository
from app.domain.common.enums import EntityType


class RelationAccess:
    def __init__(self, repository: RelationRepository) -> None:
        self._repository = repository

    async def require_project(self, user_id: UUID, project_id: UUID) -> None:
        if not await self._repository.project_exists(user_id, project_id):
            raise RelationProjectNotFound(str(project_id))

    async def require_reference(
        self,
        user_id: UUID,
        project_id: UUID,
        entity_type: EntityType,
        entity_id: UUID,
    ) -> None:
        if not await self._repository.reference_belongs_to_project(
            user_id, project_id, entity_type, entity_id
        ):
            raise RelationReferenceNotFound(str(entity_type), str(entity_id))
