from typing import Protocol
from uuid import UUID

from app.domain.common.enums import EntityType
from app.domain.relations import Relation


class RelationRepository(Protocol):
    async def project_exists(self, user_id: UUID, project_id: UUID) -> bool: ...

    async def get_by_id(
        self, user_id: UUID, project_id: UUID, relation_id: UUID
    ) -> Relation | None: ...

    async def get_by_project(
        self,
        user_id: UUID,
        project_id: UUID,
        entity_type: EntityType | None = None,
        entity_id: UUID | None = None,
    ) -> list[Relation]: ...

    async def reference_belongs_to_project(
        self,
        user_id: UUID,
        project_id: UUID,
        entity_type: EntityType,
        entity_id: UUID,
    ) -> bool: ...

    async def create(self, user_id: UUID, relation: Relation) -> None: ...

    async def update(self, user_id: UUID, relation: Relation) -> bool: ...

    async def delete(self, user_id: UUID, project_id: UUID, relation_id: UUID) -> bool: ...
