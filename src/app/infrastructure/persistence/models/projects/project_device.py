import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base

if TYPE_CHECKING:
    from app.infrastructure.persistence.models import Device, Project


class ProjectDevice(Base):
    __tablename__ = "project_devices"
    __table_args__ = (
        Index(
            "uq_project_devices_project_id_device_id",
            "project_id",
            "device_id",
            unique=True,
        ),
        {"schema": "projects"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.projects.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.devices.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    role: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="project_devices", foreign_keys=[project_id]
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="project_devices", foreign_keys=[device_id]
    )
