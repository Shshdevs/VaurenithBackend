from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.development import (
    CreateCodeComponent,
    DeleteCodeComponent,
    GetCodeComponent,
    GetRepositoryCodeComponents,
    UpdateCodeComponent,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.development.code_component import (
    provide_create_code_component,
    provide_delete_code_component,
    provide_get_code_component,
    provide_get_repository_code_components,
    provide_update_code_component,
)


def create_code_component_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateCodeComponent:
    return provide_create_code_component(session)


def get_code_component_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetCodeComponent:
    return provide_get_code_component(session)


def get_repository_code_components_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetRepositoryCodeComponents:
    return provide_get_repository_code_components(session)


def update_code_component_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateCodeComponent:
    return provide_update_code_component(session)


def delete_code_component_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteCodeComponent:
    return provide_delete_code_component(session)
