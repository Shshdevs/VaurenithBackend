from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpUnitOfWork

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.relations import (
    CreateRelation,
    DeleteRelation,
    GetProjectRelations,
    GetRelation,
    RelationNotFound,
    RelationProjectNotFound,
    RelationReferenceNotFound,
    UpdateRelation,
)
from app.domain.common.enums import EntityType, RelationOrigin, RelationType
from app.domain.identity import EmailAddress, TokenHash
from app.domain.relations import Relation


class RelationRepositoryStub:
    def __init__(self, user_id: UUID, project_id: UUID) -> None:
        self.user_id = user_id
        self.project_id = project_id
        self.relations: dict[UUID, Relation] = {}
        self.references: set[tuple[EntityType, UUID]] = set()

    async def project_exists(self, user_id: UUID, project_id: UUID) -> bool:
        return user_id == self.user_id and project_id == self.project_id

    async def reference_belongs_to_project(
        self,
        user_id: UUID,
        project_id: UUID,
        entity_type: EntityType,
        entity_id: UUID,
    ) -> bool:
        return (
            await self.project_exists(user_id, project_id)
            and (entity_type, entity_id) in self.references
        )

    async def get_by_id(self, user_id: UUID, project_id: UUID, relation_id: UUID):
        relation = self.relations.get(relation_id)
        if (
            user_id != self.user_id
            or project_id != self.project_id
            or relation is None
            or relation.project_id != project_id
        ):
            return None
        return relation

    async def get_by_project(
        self,
        user_id: UUID,
        project_id: UUID,
        entity_type: EntityType | None = None,
        entity_id: UUID | None = None,
    ) -> list[Relation]:
        if not await self.project_exists(user_id, project_id):
            return []
        relations = [
            relation
            for relation in self.relations.values()
            if relation.project_id == project_id
        ]
        if entity_type is not None and entity_id is not None:
            relations = [
                relation
                for relation in relations
                if (relation.source_entity_type, relation.source_entity_id)
                == (entity_type, entity_id)
                or (relation.target_entity_type, relation.target_entity_id)
                == (entity_type, entity_id)
            ]
        return relations

    async def create(self, user_id: UUID, relation: Relation) -> None:
        if user_id != self.user_id or relation.project_id != self.project_id:
            raise ValueError("Project not found")
        self.relations[relation.id] = relation

    async def update(self, user_id: UUID, relation: Relation) -> bool:
        if await self.get_by_id(user_id, relation.project_id, relation.id) is None:
            return False
        self.relations[relation.id] = relation
        return True

    async def delete(self, user_id: UUID, project_id: UUID, relation_id: UUID) -> bool:
        if await self.get_by_id(user_id, project_id, relation_id) is None:
            return False
        del self.relations[relation_id]
        return True


def make_identity(user_id: UUID | None = None) -> VerifiedIdentity:
    owner_id = user_id or uuid4()
    return VerifiedIdentity(
        user_id=owner_id,
        email=EmailAddress(f"{owner_id}@example.test"),
        auth_provider="relation-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


def make_relation(
    project_id: UUID,
    source: tuple[EntityType, UUID],
    target: tuple[EntityType, UUID],
    **overrides,
) -> Relation:
    now = datetime.now(UTC)
    values = {
        "entity_id": uuid4(),
        "project_id": project_id,
        "source_entity_type": source[0],
        "source_entity_id": source[1],
        "target_entity_type": target[0],
        "target_entity_id": target[1],
        "relation_type": RelationType.CONTAINS,
        "origin": RelationOrigin.USER_DEFINED,
        "confidence": None,
        "metadata": {"source": "test"},
        "created_at": now,
        "updated_at": now,
    }
    values.update(overrides)
    return Relation(**values)


def make_use_cases(identity: VerifiedIdentity, project_id: UUID):
    repository = RelationRepositoryStub(identity.user_id, project_id)
    source = (EntityType.PROJECT, project_id)
    target = (EntityType.OTHER, uuid4())
    repository.references.update({source, target})
    unit_of_work = NoOpUnitOfWork()
    return (
        repository,
        source,
        target,
        CreateRelation(repository, unit_of_work),
        GetRelation(repository),
        GetProjectRelations(repository),
        UpdateRelation(repository, unit_of_work),
        DeleteRelation(repository, unit_of_work),
    )


@pytest.mark.anyio
async def test_relation_lifecycle_and_project_entity_filtering() -> None:
    identity = make_identity()
    project_id = uuid4()
    (
        repository,
        source,
        target,
        create,
        get,
        list_relations,
        update,
        delete,
    ) = make_use_cases(identity, project_id)

    created = await create.execute(
        identity,
        project_id,
        source[0],
        source[1],
        target[0],
        target[1],
        RelationType.CONTAINS,
        confidence=Decimal("0.75"),
        metadata={"key": "value"},
    )
    assert created.origin is RelationOrigin.USER_DEFINED
    assert created.confidence == Decimal("0.75")
    assert created.metadata == {"key": "value"}

    listed = await list_relations.execute(identity, project_id)
    filtered = await list_relations.execute(identity, project_id, *target)
    assert [relation.id for relation in listed] == [created.id]
    assert [relation.id for relation in filtered] == [created.id]
    assert (await get.execute(identity, project_id, created.id)).id == created.id

    updated = await update.execute(
        identity,
        project_id,
        created.id,
        target[0],
        target[1],
        source[0],
        source[1],
        RelationType.REFERENCES,
        None,
        {"updated": True},
    )
    assert updated.relation_type is RelationType.REFERENCES
    assert updated.origin is RelationOrigin.USER_DEFINED
    assert updated.updated_at >= created.updated_at

    await delete.execute(identity, project_id, created.id)
    assert repository.relations == {}
    with pytest.raises(RelationNotFound):
        await get.execute(identity, project_id, created.id)


@pytest.mark.anyio
async def test_relation_workflows_reject_missing_project_references_and_filter_pair() -> (
    None
):
    identity = make_identity()
    project_id = uuid4()
    _, source, target, create, _, list_relations, _, _ = make_use_cases(
        identity, project_id
    )

    with pytest.raises(RelationProjectNotFound):
        await create.execute(
            identity,
            uuid4(),
            source[0],
            source[1],
            target[0],
            target[1],
            RelationType.CONTAINS,
        )
    with pytest.raises(RelationReferenceNotFound):
        await create.execute(
            identity,
            project_id,
            source[0],
            source[1],
            EntityType.DEVICE,
            uuid4(),
            RelationType.CONTAINS,
        )
    with pytest.raises(InvalidInput):
        await list_relations.execute(identity, project_id, entity_type=EntityType.PROJECT)
