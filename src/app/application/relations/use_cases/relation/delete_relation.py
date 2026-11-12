from uuid import UUID

from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.relations.exceptions import RelationNotFound
from app.application.relations.interfaces import RelationRepository
from app.application.relations.use_cases.relation.relation_access import RelationAccess


class DeleteRelation:
    def __init__(
        self,
        relation_repository: RelationRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._relations = relation_repository
        self._access = RelationAccess(relation_repository)
        self._unit_of_work = unit_of_work

    @transactional
    async def execute(
        self, identity: VerifiedIdentity, project_id: UUID, relation_id: UUID
    ) -> None:
        await self._access.require_project(identity.user_id, project_id)
        if not await self._relations.delete(identity.user_id, project_id, relation_id):
            raise RelationNotFound(str(relation_id))
