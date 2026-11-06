from app.infrastructure.persistence.repositories.identity import (
    sqlalchemy_session_repository as _session_repository,
)
from app.infrastructure.persistence.repositories.identity import (
    sqlalchemy_user_repository as _user_repository,
)

SqlAlchemySessionRepository = _session_repository.SqlAlchemySessionRepository
SqlAlchemyUserRepository = _user_repository.SqlAlchemyUserRepository

__all__ = ["SqlAlchemySessionRepository", "SqlAlchemyUserRepository"]
