import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...base import Base

if TYPE_CHECKING:
    from ..monitoring.logs_metadata import (
        LogsMetadata,
    )
    from ..projects.environment import Environment
    from ..projects.project import Project
    from .database import Database
    from .device import Device
    from .service import Service

from ...enums.infrastructure import ContainerStatus


class Container(Base):
    __tablename__ = "containers"
    __table_args__ = (
        Index(
            "uq_containers_device_id_container_runtime_id",
            "device_id",
            "container_runtime_id",
            unique=True,
        ),
        {"schema": "infrastructure"},
    )

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
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "infrastructure.services.id", deferrable=True, initially="IMMEDIATE"
        ),
    )
    container_runtime_id: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    image: Mapped[str | None] = mapped_column(String(512))
    status: Mapped[ContainerStatus] = mapped_column(
        Enum(
            ContainerStatus,
            name="container_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'unknown'"),
    )
    ports: Mapped[Any | None] = mapped_column(JSONB)
    volumes: Mapped[Any | None] = mapped_column(JSONB)
    networks: Mapped[Any | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
        "Project", back_populates="containers", foreign_keys=[project_id]
    )

    environment: Mapped["Environment"] = relationship(
        "Environment", back_populates="containers", foreign_keys=[environment_id]
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="containers", foreign_keys=[device_id]
    )

    service: Mapped["Service"] = relationship(
        "Service", back_populates="containers", foreign_keys=[service_id]
    )

    databases: Mapped[list["Database"]] = relationship(
        "Database", back_populates="container", foreign_keys="Database.container_id"
    )

    logs_metadata: Mapped[list["LogsMetadata"]] = relationship(
        "LogsMetadata",
        back_populates="container",
        foreign_keys="LogsMetadata.container_id",
    )
