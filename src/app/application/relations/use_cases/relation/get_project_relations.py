from uuid import UUID

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.relations.dto import RelationData
from app.application.relations.interfaces import RelationRepository
from app.application.relations.use_cases.relation.relation_access import RelationAccess
from app.domain.common.enums import EntityType


class GetProjectRelations:
    def __init__(
        self,
        relation_repository: RelationRepository,
    ) -> None:
        self._relations = relation_repository
        self._access = RelationAccess(relation_repository)

    async def execute(
        self,
        identity: VerifiedIdentity,
        project_id: UUID,
        entity_type: EntityType | None = None,
        entity_id: UUID | None = None,
    ) -> list[RelationData]:
        await self._access.require_project(identity.user_id, project_id)
        if (entity_type is None) != (entity_id is None):
            raise InvalidInput("entity_type and entity_id must be provided together")
        relations = await self._relations.get_by_project(
            identity.user_id, project_id, entity_type, entity_id
        )
        return [RelationData.from_relation(relation) for relation in relations]
