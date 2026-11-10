import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.slug_defaults import slug_from_name

if TYPE_CHECKING:
    from app.infrastructure.persistence.models import DeviceGroupMember
    from app.infrastructure.persistence.models.identity.user import User


class DeviceGroup(Base):
    __tablename__ = "device_groups"
    __table_args__ = (UniqueConstraint("user_id", "name"), {"schema": "infrastructure"})

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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, default=slug_from_name)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="device_groups", foreign_keys=[user_id]
    )

    device_group_members: Mapped[list["DeviceGroupMember"]] = relationship(
        "DeviceGroupMember",
        back_populates="group",
        foreign_keys="DeviceGroupMember.group_id",
        passive_deletes=True,
    )
