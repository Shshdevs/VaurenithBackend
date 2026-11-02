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
    from ..identity.client_device import (
        ClientDevice,
    )
    from ..identity.user import User

from .....domain.preferences.enums import SettingScope


class Setting(Base):
    __tablename__ = "settings"
    __table_args__ = (
        Index(
            "uq_settings_global",
            "user_id",
            "key",
            unique=True,
            postgresql_where=text("scope = 'global'"),
        ),
        Index(
            "uq_settings_client",
            "user_id",
            "client_device_id",
            "key",
            unique=True,
            postgresql_where=text("scope = 'client' AND client_device_id IS NOT NULL"),
        ),
        {"schema": "preferences"},
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
    client_device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "identity.client_devices.id", deferrable=True, initially="IMMEDIATE"
        ),
    )
    scope: Mapped[SettingScope] = mapped_column(
        Enum(
            SettingScope,
            name="setting_scope",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[Any | None] = mapped_column(JSONB)
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="settings", foreign_keys=[user_id]
    )

    client_device: Mapped["ClientDevice"] = relationship(
        "ClientDevice", back_populates="settings", foreign_keys=[client_device_id]
    )
