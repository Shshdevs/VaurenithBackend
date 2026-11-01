import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base

if TYPE_CHECKING:
    from app.infrastructure.database.models.synchronization.change_log import ChangeLog
    from app.infrastructure.database.models.identity.client_device import ClientDevice
    from app.infrastructure.database.models.infrastructure.device import Device
    from app.infrastructure.database.models.infrastructure.device_group import (
        DeviceGroup,
    )
    from app.infrastructure.database.models.monitoring.event import Event
    from app.infrastructure.database.models.monitoring.logs_metadata import LogsMetadata
    from app.infrastructure.database.models.projects.project import Project
    from app.infrastructure.database.models.identity.session import Session
    from app.infrastructure.database.models.preferences.setting import Setting
    from app.infrastructure.database.models.synchronization.sync_state import SyncState

if TYPE_CHECKING:
    from app.infrastructure.database.models.identity.client_device import ClientDevice
    from app.infrastructure.database.models.identity.session import Session


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "identity"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)

    display_name: Mapped[str | None] = mapped_column(String(255))

    auth_provider: Mapped[str | None] = mapped_column(String(100))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    sessions: Mapped[list["Session"]] = relationship("Session", back_populates="user")

    devices: Mapped[list["ClientDevice"]] = relationship(
        "ClientDevice", back_populates="user"
    )

    projects: Mapped[list["Project"]] = relationship(
        "Project", back_populates="user", foreign_keys="Project.user_id"
    )

    devices_by_user: Mapped[list["Device"]] = relationship(
        "Device", back_populates="user", foreign_keys="Device.user_id"
    )

    device_groups: Mapped[list["DeviceGroup"]] = relationship(
        "DeviceGroup", back_populates="user", foreign_keys="DeviceGroup.user_id"
    )

    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="user", foreign_keys="Event.user_id"
    )

    logs_metadata: Mapped[list["LogsMetadata"]] = relationship(
        "LogsMetadata", back_populates="user", foreign_keys="LogsMetadata.user_id"
    )

    settings: Mapped[list["Setting"]] = relationship(
        "Setting", back_populates="user", foreign_keys="Setting.user_id"
    )

    sync_state: Mapped[list["SyncState"]] = relationship(
        "SyncState", back_populates="user", foreign_keys="SyncState.user_id"
    )

    change_log_by_user: Mapped[list["ChangeLog"]] = relationship(
        "ChangeLog", back_populates="user", foreign_keys="ChangeLog.user_id"
    )

    change_log_by_changed_by_user: Mapped[list["ChangeLog"]] = relationship(
        "ChangeLog",
        back_populates="changed_by_user",
        foreign_keys="ChangeLog.changed_by_user_id",
    )
