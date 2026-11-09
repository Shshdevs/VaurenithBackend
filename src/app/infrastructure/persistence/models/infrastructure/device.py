import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    ARRAY,
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.slug_defaults import slug_from_name

if TYPE_CHECKING:
    from app.infrastructure.persistence.models import DeviceGroupMember
    from app.infrastructure.persistence.models.automation.script_execution import (
        ScriptExecution,
    )
    from app.infrastructure.persistence.models.automation.script_target import (
        ScriptTarget,
    )
    from app.infrastructure.persistence.models.identity.user import User
    from app.infrastructure.persistence.models.infrastructure.connection import (
        Connection,
    )
    from app.infrastructure.persistence.models.infrastructure.container import Container
    from app.infrastructure.persistence.models.infrastructure.database import Database
    from app.infrastructure.persistence.models.infrastructure.service import Service
    from app.infrastructure.persistence.models.monitoring.event import Event
    from app.infrastructure.persistence.models.monitoring.logs_metadata import (
        LogsMetadata,
    )
    from app.infrastructure.persistence.models.monitoring.metric import Metric
    from app.infrastructure.persistence.models.projects.project_device import (
        ProjectDevice,
    )

from app.domain.infrastructure.enums import DeviceType


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = {"schema": "infrastructure"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, default=slug_from_name)
    hostname: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    device_type: Mapped[DeviceType] = mapped_column(
        Enum(
            DeviceType,
            name="device_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    operating_system: Mapped[str | None] = mapped_column(String(100))
    os_version: Mapped[str | None] = mapped_column(String(100))
    architecture: Mapped[str | None] = mapped_column(String(50))
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(Text))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    project_devices: Mapped[list["ProjectDevice"]] = relationship(
        "ProjectDevice", back_populates="device", foreign_keys="ProjectDevice.device_id"
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="devices_by_user", foreign_keys=[user_id]
    )

    connections: Mapped[list["Connection"]] = relationship(
        "Connection", back_populates="device", foreign_keys="Connection.device_id"
    )

    services: Mapped[list["Service"]] = relationship(
        "Service", back_populates="device", foreign_keys="Service.device_id"
    )

    containers: Mapped[list["Container"]] = relationship(
        "Container", back_populates="device", foreign_keys="Container.device_id"
    )

    databases: Mapped[list["Database"]] = relationship(
        "Database", back_populates="device", foreign_keys="Database.device_id"
    )

    device_group_members: Mapped[list["DeviceGroupMember"]] = relationship(
        "DeviceGroupMember",
        back_populates="device",
        foreign_keys="DeviceGroupMember.device_id",
        passive_deletes=True,
    )

    script_targets: Mapped[list["ScriptTarget"]] = relationship(
        "ScriptTarget", back_populates="device", foreign_keys="ScriptTarget.device_id"
    )

    script_executions: Mapped[list["ScriptExecution"]] = relationship(
        "ScriptExecution",
        back_populates="device",
        foreign_keys="ScriptExecution.device_id",
    )

    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="device", foreign_keys="Event.device_id"
    )

    metrics: Mapped[list["Metric"]] = relationship(
        "Metric", back_populates="device", foreign_keys="Metric.device_id"
    )

    logs_metadata: Mapped[list["LogsMetadata"]] = relationship(
        "LogsMetadata", back_populates="device", foreign_keys="LogsMetadata.device_id"
    )
