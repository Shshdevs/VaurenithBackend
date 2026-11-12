from app.infrastructure.persistence.repositories.identity import (
    sqlalchemy_client_device_repository as _client_device_repository,
)
from app.infrastructure.persistence.repositories.identity import (
    sqlalchemy_session_repository as _session_repository,
)
from app.infrastructure.persistence.repositories.identity import (
    sqlalchemy_user_repository as _user_repository,
)

SqlAlchemyClientDeviceRepository = (
    _client_device_repository.SqlAlchemyClientDeviceRepository
)
SqlAlchemySessionRepository = _session_repository.SqlAlchemySessionRepository
SqlAlchemyUserRepository = _user_repository.SqlAlchemyUserRepository

__all__ = [
    "SqlAlchemyClientDeviceRepository",
    "SqlAlchemySessionRepository",
    "SqlAlchemyUserRepository",
]
