import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.identity.user import User
    from app.infrastructure.database.models.infrastructure.container import Container
    from app.infrastructure.database.models.infrastructure.device import Device
    from app.infrastructure.database.models.infrastructure.service import Service
    from app.infrastructure.database.models.projects.project import Project


class LogsMetadata(Base):
    __tablename__ = "logs_metadata"
    __table_args__ = {"schema": "monitoring"}

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
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.projects.id", deferrable=True, initially="IMMEDIATE"),
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.devices.id", deferrable=True, initially="IMMEDIATE"),
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "infrastructure.services.id", deferrable=True, initially="IMMEDIATE"
        ),
    )
    container_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "infrastructure.containers.id", deferrable=True, initially="IMMEDIATE"
        ),
    )
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    reference: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str | None] = mapped_column(String(50))
    records_count: Mapped[int | None] = mapped_column(BigInteger)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="logs_metadata", foreign_keys=[user_id]
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="logs_metadata", foreign_keys=[project_id]
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="logs_metadata", foreign_keys=[device_id]
    )

    service: Mapped["Service"] = relationship(
        "Service", back_populates="logs_metadata", foreign_keys=[service_id]
    )

    container: Mapped["Container"] = relationship(
        "Container", back_populates="logs_metadata", foreign_keys=[container_id]
    )
