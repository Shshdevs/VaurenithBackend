import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    Index,
    DateTime,
    ForeignKey,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.infrastructure.device import Device
    from app.infrastructure.database.models.projects.environment import Environment
    from app.infrastructure.database.models.automation.script import Script


class ScriptTarget(Base):
    __tablename__ = "script_targets"
    __table_args__ = (
        Index(
            "uq_script_targets_script_id_device_id_environment_id",
            "script_id",
            "device_id",
            "environment_id",
            unique=True,
        ),
        {"schema": "automation"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    script_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automation.scripts.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.devices.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    environment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.environments.id", deferrable=True, initially="IMMEDIATE"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    script: Mapped["Script"] = relationship(
        "Script", back_populates="script_targets", foreign_keys=[script_id]
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="script_targets", foreign_keys=[device_id]
    )

    environment: Mapped["Environment"] = relationship(
        "Environment", back_populates="script_targets", foreign_keys=[environment_id]
    )
