from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.development import (
    CreateBranch,
    DeleteBranch,
    GetBranch,
    GetRepositoryBranches,
    UpdateBranch,
)
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.development.branch import (
    provide_create_branch,
    provide_delete_branch,
    provide_get_branch,
    provide_get_repository_branches,
    provide_update_branch,
)


def create_branch_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateBranch:
    return provide_create_branch(session)


def get_branch_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetBranch:
    return provide_get_branch(session)


def get_repository_branches_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetRepositoryBranches:
    return provide_get_repository_branches(session)


def update_branch_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> UpdateBranch:
    return provide_update_branch(session)


def delete_branch_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> DeleteBranch:
    return provide_delete_branch(session)
