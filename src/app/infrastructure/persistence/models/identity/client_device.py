import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...base import Base

if TYPE_CHECKING:
    from ..automation.script_execution import (
        ScriptExecution,
    )
    from ..monitoring.event import Event
    from ..preferences.setting import Setting
    from ..synchronization.change_log import (
        ChangeLog,
    )
    from ..synchronization.sync_state import (
        SyncState,
    )
    from .session import Session
    from .user import User
from .....domain.identity.enums import (
    ClientDeviceStatus,
    PlatformType,
)

if TYPE_CHECKING:
    from .session import Session
    from .user import User


class ClientDevice(Base):
    __tablename__ = "client_devices"
    __table_args__ = {"schema": "identity"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("identity.users.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    platform: Mapped[PlatformType] = mapped_column(
        SQLAlchemyEnum(
            PlatformType,
            name="platform_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )

    app_version: Mapped[str | None] = mapped_column(String(50))

    status: Mapped[ClientDeviceStatus] = mapped_column(
        SQLAlchemyEnum(
            ClientDeviceStatus,
            name="client_device_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'active'"),
    )

    registered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="devices")

    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="client_device"
    )

    script_executions: Mapped[list["ScriptExecution"]] = relationship(
        "ScriptExecution",
        back_populates="client_device",
        foreign_keys="ScriptExecution.client_device_id",
    )

    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="client_device", foreign_keys="Event.client_device_id"
    )

    settings: Mapped[list["Setting"]] = relationship(
        "Setting",
        back_populates="client_device",
        foreign_keys="Setting.client_device_id",
    )

    sync_state: Mapped[list["SyncState"]] = relationship(
        "SyncState",
        back_populates="client_device",
        foreign_keys="SyncState.client_device_id",
    )

    change_log: Mapped[list["ChangeLog"]] = relationship(
        "ChangeLog",
        back_populates="changed_by_client",
        foreign_keys="ChangeLog.changed_by_client_id",
    )
