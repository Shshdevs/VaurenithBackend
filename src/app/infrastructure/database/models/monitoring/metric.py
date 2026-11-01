import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.infrastructure.device import Device

from app.infrastructure.database.enums.monitoring import MetricType, MetricUnit


class Metric(Base):
    __tablename__ = "metrics"
    __table_args__ = (
        Index(
            "ix_metrics_device_id_metric_type_collected_at",
            "device_id",
            "metric_type",
            "collected_at",
        ),
        CheckConstraint("value >= 0", name="ck_metrics_nonnegative"),
        {"schema": "monitoring"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.devices.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    metric_type: Mapped[MetricType] = mapped_column(
        Enum(
            MetricType,
            name="metric_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    unit: Mapped[MetricUnit] = mapped_column(
        Enum(
            MetricUnit,
            name="metric_unit",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    source: Mapped[str | None] = mapped_column(String(255))
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="metrics", foreign_keys=[device_id]
    )
