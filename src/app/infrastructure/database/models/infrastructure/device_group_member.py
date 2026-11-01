import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.infrastructure.device import Device
    from app.infrastructure.database.models.infrastructure.device_group import (
        DeviceGroup,
    )


class DeviceGroupMember(Base):
    __tablename__ = "device_group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "device_id"),
        {"schema": "infrastructure"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.device_groups.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.devices.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    group: Mapped["DeviceGroup"] = relationship(
        "DeviceGroup", back_populates="device_group_members", foreign_keys=[group_id]
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="device_group_members", foreign_keys=[device_id]
    )
