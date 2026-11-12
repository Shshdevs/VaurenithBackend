from sqlalchemy.ext.asyncio import AsyncSession

from app.application.development import (
    CreateBranch,
    DeleteBranch,
    GetBranch,
    GetRepositoryBranches,
    UpdateBranch,
)
from app.infrastructure.persistence.repositories.development import (
    SqlAlchemyBranchRepository,
    SqlAlchemyRepositoryRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_branch(session: AsyncSession) -> CreateBranch:
    return CreateBranch(
        SqlAlchemyBranchRepository(session),
        SqlAlchemyRepositoryRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_branch(session: AsyncSession) -> GetBranch:
    return GetBranch(SqlAlchemyBranchRepository(session))


def provide_get_repository_branches(session: AsyncSession) -> GetRepositoryBranches:
    return GetRepositoryBranches(
        SqlAlchemyBranchRepository(session),
        SqlAlchemyRepositoryRepository(session),
    )


def provide_update_branch(session: AsyncSession) -> UpdateBranch:
    return UpdateBranch(SqlAlchemyBranchRepository(session), SqlAlchemyUnitOfWork(session))


def provide_delete_branch(session: AsyncSession) -> DeleteBranch:
    return DeleteBranch(SqlAlchemyBranchRepository(session), SqlAlchemyUnitOfWork(session))
