import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Identity,
    Index,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...base import Base

if TYPE_CHECKING:
    from ..identity.client_device import (
        ClientDevice,
    )
    from ..identity.user import User

from .....domain.common.enums import EntityType
from .....domain.synchronization.enums import ChangeOperation


class ChangeLog(Base):
    __tablename__ = "change_log"
    __table_args__ = (
        Index(
            "uq_change_log_entity_type_entity_id_version",
            "entity_type",
            "entity_id",
            "version",
            unique=True,
        ),
        Index("ix_change_log_user_id_created_at", "user_id", "created_at"),
        Index("uq_change_log_sequence", "sequence", unique=True),
        Index("ix_change_log_user_sequence", "user_id", "sequence"),
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
    entity_type: Mapped[EntityType] = mapped_column(
        Enum(
            EntityType,
            name="entity_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    operation: Mapped[ChangeOperation] = mapped_column(
        Enum(
            ChangeOperation,
            name="change_operation",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sequence: Mapped[int] = mapped_column(
        BigInteger, Identity(always=True), nullable=False
    )
    changed_by_client_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "identity.client_devices.id", deferrable=True, initially="IMMEDIATE"
        ),
    )
    changed_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    payload: Mapped[Any | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="change_log_by_user", foreign_keys=[user_id]
    )

    changed_by_client: Mapped["ClientDevice"] = relationship(
        "ClientDevice", back_populates="change_log", foreign_keys=[changed_by_client_id]
    )

    changed_by_user: Mapped["User"] = relationship(
        "User",
        back_populates="change_log_by_changed_by_user",
        foreign_keys=[changed_by_user_id],
    )
