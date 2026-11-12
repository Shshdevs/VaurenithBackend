from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.development import CreateCommit, GetCommit, GetRepositoryCommits
from app.bootstrap.dependencies.database import get_database_session
from app.bootstrap.providers.development.commit import (
    provide_create_commit,
    provide_get_commit,
    provide_get_repository_commits,
)


def create_commit_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> CreateCommit:
    return provide_create_commit(session)


def get_commit_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetCommit:
    return provide_get_commit(session)


def get_repository_commits_dependency(
    session: AsyncSession = Depends(get_database_session, scope="function"),
) -> GetRepositoryCommits:
    return provide_get_repository_commits(session)
