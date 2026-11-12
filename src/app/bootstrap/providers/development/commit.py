from sqlalchemy.ext.asyncio import AsyncSession

from app.application.development import CreateCommit, GetCommit, GetRepositoryCommits
from app.infrastructure.persistence.repositories.development import (
    SqlAlchemyCommitRepository,
    SqlAlchemyRepositoryRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_commit(session: AsyncSession) -> CreateCommit:
    return CreateCommit(
        SqlAlchemyCommitRepository(session),
        SqlAlchemyRepositoryRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_commit(session: AsyncSession) -> GetCommit:
    return GetCommit(SqlAlchemyCommitRepository(session))


def provide_get_repository_commits(session: AsyncSession) -> GetRepositoryCommits:
    return GetRepositoryCommits(
        SqlAlchemyCommitRepository(session),
        SqlAlchemyRepositoryRepository(session),
    )
