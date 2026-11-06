import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.infrastructure.device import Device

from app.domain.infrastructure.enums import (
    AuthenticationType,
    ConnectionStatus,
)


class Connection(Base):
    __tablename__ = "connections"
    __table_args__ = (
        Index(
            "uq_connections_one_default_per_device",
            "device_id",
            unique=True,
            postgresql_where=text("is_default = TRUE"),
        ),
        CheckConstraint("port BETWEEN 1 AND 65535", name="ck_connections_port"),
        CheckConstraint("connection_timeout > 0", name="ck_connections_timeout"),
        {"schema": "infrastructure"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.devices.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    host: Mapped[str] = mapped_column(String(512), nullable=False)
    port: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("22")
    )
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    authentication_type: Mapped[AuthenticationType] = mapped_column(
        Enum(
            AuthenticationType,
            name="authentication_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    connection_timeout: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("30")
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    last_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[ConnectionStatus] = mapped_column(
        Enum(
            ConnectionStatus,
            name="connection_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'unknown'"),
    )
    last_error: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="connections", foreign_keys=[device_id]
    )
