from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.relations.dto import RelationData
from app.application.relations.interfaces import RelationRepository
from app.application.relations.use_cases.relation.relation_access import RelationAccess
from app.domain.common.enums import EntityType, RelationOrigin, RelationType
from app.domain.relations import Relation
from app.domain.relations.exceptions import InvalidRelation


class CreateRelation:
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
        self,
        identity: VerifiedIdentity,
        project_id: UUID,
        source_entity_type: EntityType,
        source_entity_id: UUID,
        target_entity_type: EntityType,
        target_entity_id: UUID,
        relation_type: RelationType,
        confidence: Decimal | None = None,
        metadata: Any | None = None,
    ) -> RelationData:
        await self._access.require_project(identity.user_id, project_id)
        await self._access.require_reference(
            identity.user_id, project_id, source_entity_type, source_entity_id
        )
        await self._access.require_reference(
            identity.user_id, project_id, target_entity_type, target_entity_id
        )
        now = datetime.now(UTC)
        try:
            relation = Relation(
                entity_id=uuid4(),
                project_id=project_id,
                source_entity_type=EntityType(source_entity_type),
                source_entity_id=source_entity_id,
                target_entity_type=EntityType(target_entity_type),
                target_entity_id=target_entity_id,
                relation_type=RelationType(relation_type),
                origin=RelationOrigin.USER_DEFINED,
                confidence=confidence,
                metadata=metadata,
                created_at=now,
                updated_at=now,
            )
        except (InvalidRelation, ValueError) as error:
            raise InvalidInput(str(error)) from error
        await self._relations.create(identity.user_id, relation)
        return RelationData.from_relation(relation)
