from sqlalchemy.ext.asyncio import AsyncSession

from app.application.development import (
    CreateDependency,
    DeleteDependency,
    GetComponentDependencies,
    GetDependency,
    GetRepositoryDependencies,
    UpdateDependency,
)
from app.infrastructure.persistence.repositories.development import (
    SqlAlchemyCodeComponentRepository,
    SqlAlchemyDependencyRepository,
    SqlAlchemyRepositoryRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_dependency(session: AsyncSession) -> CreateDependency:
    return CreateDependency(
        SqlAlchemyDependencyRepository(session),
        SqlAlchemyCodeComponentRepository(session),
        SqlAlchemyRepositoryRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_dependency(session: AsyncSession) -> GetDependency:
    return GetDependency(SqlAlchemyDependencyRepository(session))


def provide_get_component_dependencies(
    session: AsyncSession,
) -> GetComponentDependencies:
    return GetComponentDependencies(
        SqlAlchemyDependencyRepository(session),
        SqlAlchemyCodeComponentRepository(session),
    )


def provide_get_repository_dependencies(
    session: AsyncSession,
) -> GetRepositoryDependencies:
    return GetRepositoryDependencies(
        SqlAlchemyDependencyRepository(session),
        SqlAlchemyRepositoryRepository(session),
    )


def provide_update_dependency(session: AsyncSession) -> UpdateDependency:
    return UpdateDependency(
        SqlAlchemyDependencyRepository(session),
        SqlAlchemyCodeComponentRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_delete_dependency(session: AsyncSession) -> DeleteDependency:
    return DeleteDependency(
        SqlAlchemyDependencyRepository(session), SqlAlchemyUnitOfWork(session)
    )
