import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.slug_defaults import slug_from_name

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.infrastructure.container import Container
    from app.infrastructure.persistence.models.infrastructure.device import Device
    from app.infrastructure.persistence.models.infrastructure.service import Service
    from app.infrastructure.persistence.models.projects.environment import Environment
    from app.infrastructure.persistence.models.projects.project import Project

from app.domain.infrastructure.enums import DbmsType, ResourceStatus


class Database(Base):
    __tablename__ = "databases"
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
    container_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.containers.id", deferrable=True, initially="IMMEDIATE"),
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.services.id", deferrable=True, initially="IMMEDIATE"),
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, default=slug_from_name)
    dbms_type: Mapped[DbmsType] = mapped_column(
        Enum(
            DbmsType,
            name="dbms_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    host: Mapped[str | None] = mapped_column(String(512))
    port: Mapped[int | None] = mapped_column(Integer)
    database_name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[ResourceStatus] = mapped_column(
        Enum(
            ResourceStatus,
            name="resource_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'unknown'"),
    )
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
        "Project", back_populates="databases", foreign_keys=[project_id]
    )

    environment: Mapped["Environment"] = relationship(
        "Environment", back_populates="databases", foreign_keys=[environment_id]
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="databases", foreign_keys=[device_id]
    )

    container: Mapped["Container"] = relationship(
        "Container", back_populates="databases", foreign_keys=[container_id]
    )

    service: Mapped["Service"] = relationship(
        "Service", back_populates="databases", foreign_keys=[service_id]
    )
