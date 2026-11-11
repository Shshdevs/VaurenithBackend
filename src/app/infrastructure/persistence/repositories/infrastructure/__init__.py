from app.infrastructure.persistence.repositories.infrastructure import (
    sqlalchemy_connection_repository as _connection_repository,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    sqlalchemy_container_repository as _container_repository,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    sqlalchemy_device_group_repository as _device_group_repository,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    sqlalchemy_device_repository as _device_repository,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    sqlalchemy_service_repository as _service_repository,
)

SqlAlchemyDeviceRepository = _device_repository.SqlAlchemyDeviceRepository
SqlAlchemyDeviceGroupRepository = _device_group_repository.SqlAlchemyDeviceGroupRepository
SqlAlchemyServiceRepository = _service_repository.SqlAlchemyServiceRepository
SqlAlchemyContainerRepository = _container_repository.SqlAlchemyContainerRepository
SqlAlchemyConnectionRepository = _connection_repository.SqlAlchemyConnectionRepository

__all__ = [
    "SqlAlchemyContainerRepository",
    "SqlAlchemyConnectionRepository",
    "SqlAlchemyDeviceRepository",
    "SqlAlchemyDeviceGroupRepository",
    "SqlAlchemyServiceRepository",
]
