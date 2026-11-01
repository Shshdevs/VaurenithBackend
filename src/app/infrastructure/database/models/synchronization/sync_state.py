import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    Index,
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.identity.client_device import ClientDevice
    from app.infrastructure.database.models.identity.user import User

from app.infrastructure.database.enums.synchronization import SyncStatus
from app.infrastructure.database.enums.common import EntityType


class SyncState(Base):
    __tablename__ = "sync_state"
    __table_args__ = (
        Index("ix_sync_state_user_id_client_device_id", "user_id", "client_device_id"),
        Index(
            "uq_sync_state_entity",
            "client_device_id",
            "entity_type",
            "entity_id",
            unique=True,
            postgresql_where=text("entity_type IS NOT NULL AND entity_id IS NOT NULL"),
        ),
        Index(
            "uq_sync_state_device",
            "user_id",
            "client_device_id",
            unique=True,
            postgresql_where=text("entity_type IS NULL AND entity_id IS NULL"),
        ),
        {"schema": "synchronization"},
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
    client_device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "identity.client_devices.id", deferrable=True, initially="IMMEDIATE"
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
    local_version: Mapped[int | None] = mapped_column(BigInteger)
    server_version: Mapped[int | None] = mapped_column(BigInteger)
    status: Mapped[SyncStatus] = mapped_column(
        Enum(
            SyncStatus,
            name="sync_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'pending'"),
    )
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="sync_state", foreign_keys=[user_id]
    )

    client_device: Mapped["ClientDevice"] = relationship(
        "ClientDevice", back_populates="sync_state", foreign_keys=[client_device_id]
    )
