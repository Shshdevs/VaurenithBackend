import uuid
from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import (
    ForeignKey,
    UniqueConstraint,
    DateTime,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.infrastructure.device_group_member import (
        DeviceGroupMember,
    )
    from app.infrastructure.database.models.identity.user import User


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
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
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
