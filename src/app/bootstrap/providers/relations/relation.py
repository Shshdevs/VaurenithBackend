from sqlalchemy.ext.asyncio import AsyncSession

from app.application.relations import (
    CreateRelation,
    DeleteRelation,
    GetProjectRelations,
    GetRelation,
    UpdateRelation,
)
from app.infrastructure.persistence.repositories.relations import (
    SqlAlchemyRelationRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_relation(session: AsyncSession) -> CreateRelation:
    return CreateRelation(
        SqlAlchemyRelationRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_relation(session: AsyncSession) -> GetRelation:
    return GetRelation(
        SqlAlchemyRelationRepository(session),
    )


def provide_get_project_relations(session: AsyncSession) -> GetProjectRelations:
    return GetProjectRelations(
        SqlAlchemyRelationRepository(session),
    )


def provide_update_relation(session: AsyncSession) -> UpdateRelation:
    return UpdateRelation(
        SqlAlchemyRelationRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_relation(session: AsyncSession) -> DeleteRelation:
    return DeleteRelation(
        SqlAlchemyRelationRepository(session),
        SqlAlchemyUnitOfWork(session),
    )
