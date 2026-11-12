from uuid import UUID

from app.application.identity import VerifiedIdentity
from app.application.relations.dto import RelationData
from app.application.relations.exceptions import RelationNotFound
from app.application.relations.interfaces import RelationRepository
from app.application.relations.use_cases.relation.relation_access import RelationAccess


class GetRelation:
    def __init__(
        self,
        relation_repository: RelationRepository,
    ) -> None:
        self._relations = relation_repository
        self._access = RelationAccess(relation_repository)

    async def execute(
        self, identity: VerifiedIdentity, project_id: UUID, relation_id: UUID
    ) -> RelationData:
        await self._access.require_project(identity.user_id, project_id)
        relation = await self._relations.get_by_id(
            identity.user_id, project_id, relation_id
        )
        if relation is None:
            raise RelationNotFound(str(relation_id))
        return RelationData.from_relation(relation)
