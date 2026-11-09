from app.infrastructure.persistence.repositories.projects import (
    sqlalchemy_environment_repository as _environment_repository,
)
from app.infrastructure.persistence.repositories.projects import (
    sqlalchemy_project_device_repository as _project_device_repository,
)
from app.infrastructure.persistence.repositories.projects import (
    sqlalchemy_project_repository as _project_repository,
)

SqlAlchemyProjectRepository = _project_repository.SqlAlchemyProjectRepository
SqlAlchemyEnvironmentRepository = _environment_repository.SqlAlchemyEnvironmentRepository
SqlAlchemyProjectDeviceRepository = (
    _project_device_repository.SqlAlchemyProjectDeviceRepository
)
__all__ = [
    "SqlAlchemyProjectRepository",
    "SqlAlchemyEnvironmentRepository",
    "SqlAlchemyProjectDeviceRepository",
]
