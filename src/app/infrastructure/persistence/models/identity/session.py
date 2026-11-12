import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.identity.client_device import (
        ClientDevice,
    )
    from app.infrastructure.persistence.models.identity.user import User

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.identity.client_device import (
        ClientDevice,
    )
    from app.infrastructure.persistence.models.identity.user import User


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        ForeignKeyConstraint(
            ["user_id", "client_device_id"],
            ["identity.client_devices.user_id", "identity.client_devices.id"],
            name="fk_sessions_user_client_device",
            deferrable=True,
            initially="IMMEDIATE",
        ),
        Index(
            "ix_sessions_client_device_revoked_expires",
            "client_device_id",
            "revoked_at",
            "expires_at",
        ),
        UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
        {"schema": "identity"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    client_device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    token_hash: Mapped[str] = mapped_column(String(512), nullable=False)

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="sessions", foreign_keys=[user_id]
    )

    client_device: Mapped["ClientDevice"] = relationship(
        "ClientDevice",
        back_populates="sessions",
        primaryjoin=(
            "and_(Session.client_device_id == ClientDevice.id, "
            "Session.user_id == ClientDevice.user_id)"
        ),
        foreign_keys=[client_device_id],
    )
