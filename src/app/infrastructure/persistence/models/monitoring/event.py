import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.identity.client_device import (
        ClientDevice,
    )
    from app.infrastructure.persistence.models.identity.user import User
    from app.infrastructure.persistence.models.infrastructure.device import Device
    from app.infrastructure.persistence.models.projects.project import Project

from app.domain.common.enums import EntityType
from app.domain.monitoring.enums import EventResult, EventType


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        Index("ix_events_project_id_created_at", "project_id", "created_at"),
        Index("ix_events_device_id_created_at", "device_id", "created_at"),
        Index("ix_events_event_type_created_at", "event_type", "created_at"),
        {"schema": "monitoring"},
    )

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
    event_type: Mapped[EventType] = mapped_column(
        Enum(
            EventType,
            name="event_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    entity_type: Mapped[EntityType | None] = mapped_column(
        Enum(
            EntityType,
            name="entity_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        )
    )
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    description: Mapped[str | None] = mapped_column(Text)
    result: Mapped[EventResult] = mapped_column(
        Enum(
            EventResult,
            name="event_result",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    metadata_: Mapped[Any | None] = mapped_column("metadata", JSONB)
    client_device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "identity.client_devices.id", deferrable=True, initially="IMMEDIATE"
        ),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="events", foreign_keys=[user_id]
    )

    project: Mapped["Project"] = relationship(
        "Project", back_populates="events", foreign_keys=[project_id]
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="events", foreign_keys=[device_id]
    )

    client_device: Mapped["ClientDevice"] = relationship(
        "ClientDevice", back_populates="events", foreign_keys=[client_device_id]
    )
