import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.infrastructure.container import Container
    from app.infrastructure.database.models.infrastructure.database import Database
    from app.infrastructure.database.models.infrastructure.device import Device
    from app.infrastructure.database.models.monitoring.logs_metadata import LogsMetadata
    from app.infrastructure.database.models.projects.environment import Environment
    from app.infrastructure.database.models.projects.project import Project

from app.infrastructure.database.enums.infrastructure import ResourceStatus, ServiceType


class Service(Base):
    __tablename__ = "services"
    __table_args__ = {"schema": "infrastructure"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.projects.id", deferrable=True, initially="IMMEDIATE"),
    )
    environment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.environments.id", deferrable=True, initially="IMMEDIATE"),
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.devices.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    service_type: Mapped[ServiceType] = mapped_column(
        Enum(
            ServiceType,
            name="service_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text)
    system_identifier: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[ResourceStatus] = mapped_column(
        Enum(
            ResourceStatus,
            name="resource_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'unknown'"),
    )
    last_status_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[Any | None] = mapped_column("metadata", JSONB)
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="services", foreign_keys=[project_id]
    )

    environment: Mapped["Environment"] = relationship(
        "Environment", back_populates="services", foreign_keys=[environment_id]
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="services", foreign_keys=[device_id]
    )

    containers: Mapped[list["Container"]] = relationship(
        "Container", back_populates="service", foreign_keys="Container.service_id"
    )

    databases: Mapped[list["Database"]] = relationship(
        "Database", back_populates="service", foreign_keys="Database.service_id"
    )

    logs_metadata: Mapped[list["LogsMetadata"]] = relationship(
        "LogsMetadata", back_populates="service", foreign_keys="LogsMetadata.service_id"
    )
