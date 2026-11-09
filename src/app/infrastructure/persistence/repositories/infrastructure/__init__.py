from app.infrastructure.persistence.repositories.infrastructure import (
    sqlalchemy_device_group_repository as _device_group_repository,
)
from app.infrastructure.persistence.repositories.infrastructure import (
    sqlalchemy_device_repository as _device_repository,
)

SqlAlchemyDeviceRepository = _device_repository.SqlAlchemyDeviceRepository
SqlAlchemyDeviceGroupRepository = _device_group_repository.SqlAlchemyDeviceGroupRepository

__all__ = ["SqlAlchemyDeviceRepository", "SqlAlchemyDeviceGroupRepository"]
