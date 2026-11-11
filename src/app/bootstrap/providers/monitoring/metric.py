from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monitoring import CreateMetric, GetDeviceMetrics
from app.infrastructure.persistence.repositories.infrastructure import (
    SqlAlchemyDeviceRepository,
)
from app.infrastructure.persistence.repositories.monitoring import (
    SqlAlchemyMetricRepository,
)
from app.infrastructure.persistence.sqlalchemy_unit_of_work import SqlAlchemyUnitOfWork


def provide_create_metric(session: AsyncSession) -> CreateMetric:
    return CreateMetric(
        SqlAlchemyMetricRepository(session),
        SqlAlchemyDeviceRepository(session),
        SqlAlchemyUnitOfWork(session),
    )


def provide_get_device_metrics(session: AsyncSession) -> GetDeviceMetrics:
    return GetDeviceMetrics(
        SqlAlchemyMetricRepository(session),
        SqlAlchemyDeviceRepository(session),
    )
