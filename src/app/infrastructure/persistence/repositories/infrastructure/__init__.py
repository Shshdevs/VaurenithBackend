from app.infrastructure.persistence.repositories.infrastructure import (
    sqlalchemy_device_group_repository as _device_group_repository,
)

SqlAlchemyDeviceGroupRepository = _device_group_repository.SqlAlchemyDeviceGroupRepository

__all__ = ["SqlAlchemyDeviceGroupRepository"]
