from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from tests.support import NoOpUnitOfWork

from app.application.common.exceptions import InvalidInput
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceNotFound
from app.application.monitoring.use_cases import CreateMetric, GetDeviceMetrics
from app.domain.identity import EmailAddress, TokenHash
from app.domain.monitoring import Metric, MetricType, MetricUnit


class DeviceRepositoryStub:
    def __init__(self, device_id: UUID) -> None:
        self.device_id = device_id

    async def get_by_id(self, identity: VerifiedIdentity, device_id: UUID):
        return object() if device_id == self.device_id else None


class MetricRepositoryStub:
    def __init__(self) -> None:
        self.metrics: list[Metric] = []

    async def create(self, metric: Metric) -> None:
        self.metrics.append(metric)

    async def get_for_device(self, device_id, start, end, limit, offset):
        values = [metric for metric in self.metrics if metric.device_id == device_id]
        if start is not None:
            values = [metric for metric in values if metric.collected_at >= start]
        if end is not None:
            values = [metric for metric in values if metric.collected_at < end]
        return sorted(values, key=lambda metric: metric.collected_at, reverse=True)[
            offset : offset + limit
        ]


def make_identity() -> VerifiedIdentity:
    user_id = uuid4()
    return VerifiedIdentity(
        user_id=user_id,
        email=EmailAddress(f"{user_id}@example.test"),
        auth_provider="monitoring-test",
        expires_at=datetime.now(UTC) + timedelta(hours=1),
        token_hash=TokenHash("a" * 64),
    )


@pytest.mark.anyio
async def test_create_and_read_metrics_for_owned_device_in_time_range() -> None:
    identity = make_identity()
    device_id = uuid4()
    metric_repository = MetricRepositoryStub()
    device_repository = DeviceRepositoryStub(device_id)
    create_metric = CreateMetric(metric_repository, device_repository, NoOpUnitOfWork())
    get_metrics = GetDeviceMetrics(metric_repository, device_repository)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    first = await create_metric.create_metric(
        identity,
        device_id,
        MetricType.CPU_USAGE,
        Decimal("14.25"),
        MetricUnit.PERCENT,
        start,
        "agent",
    )
    await create_metric.create_metric(
        identity,
        device_id,
        MetricType.CPU_USAGE,
        Decimal("21.5"),
        MetricUnit.PERCENT,
        start + timedelta(minutes=1),
        "agent",
    )

    results = await get_metrics.get_device_metrics(
        identity, device_id, start, start + timedelta(minutes=1), 100, 0
    )

    assert first.value == Decimal("14.250000")
    assert len(results) == 1
    assert results[0].value == Decimal("14.250000")
    assert results[0].device_id == device_id


@pytest.mark.anyio
async def test_metric_operations_reject_unowned_device_and_invalid_range() -> None:
    identity = make_identity()
    owned_device_id = uuid4()
    metric_repository = MetricRepositoryStub()
    device_repository = DeviceRepositoryStub(owned_device_id)
    create_metric = CreateMetric(metric_repository, device_repository, NoOpUnitOfWork())
    get_metrics = GetDeviceMetrics(metric_repository, device_repository)

    with pytest.raises(DeviceNotFound):
        await create_metric.create_metric(
            identity,
            uuid4(),
            MetricType.CPU_USAGE,
            Decimal("1"),
            MetricUnit.PERCENT,
            datetime.now(UTC),
            None,
        )
    with pytest.raises(InvalidInput, match="range start must precede end"):
        await get_metrics.get_device_metrics(
            identity,
            owned_device_id,
            datetime(2026, 2, 1, tzinfo=UTC),
            datetime(2026, 1, 1, tzinfo=UTC),
            100,
            0,
        )
