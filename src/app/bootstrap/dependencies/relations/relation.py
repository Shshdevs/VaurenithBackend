from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.relations import (
    CreateRelation,
    DeleteRelation,
    GetProjectRelations,
    GetRelation,
    UpdateRelation,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.relations import (
    provide_create_relation,
    provide_delete_relation,
    provide_get_project_relations,
    provide_get_relation,
    provide_update_relation,
)


def create_relation_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateRelation:
    return provide_create_relation(session)


def get_relation_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetRelation:
    return provide_get_relation(session)


def get_project_relations_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetProjectRelations:
    return provide_get_project_relations(session)


def update_relation_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateRelation:
    return provide_update_relation(session)


def delete_relation_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteRelation:
    return provide_delete_relation(session)
