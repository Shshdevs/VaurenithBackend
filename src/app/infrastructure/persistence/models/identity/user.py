import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.slug_defaults import nickname_from_user

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.automation.script import Script
    from app.infrastructure.persistence.models.identity.client_device import (
        ClientDevice,
    )
    from app.infrastructure.persistence.models.identity.session import Session
    from app.infrastructure.persistence.models.infrastructure.device import Device
    from app.infrastructure.persistence.models.infrastructure.device_group import (
        DeviceGroup,
    )
    from app.infrastructure.persistence.models.monitoring.event import Event
    from app.infrastructure.persistence.models.monitoring.logs_metadata import (
        LogsMetadata,
    )
    from app.infrastructure.persistence.models.preferences.setting import Setting
    from app.infrastructure.persistence.models.projects.project import Project
    from app.infrastructure.persistence.models.synchronization.change_log import (
        ChangeLog,
    )
    from app.infrastructure.persistence.models.synchronization.sync_state import (
        SyncState,
    )

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.identity.client_device import (
        ClientDevice,
    )
    from app.infrastructure.persistence.models.identity.session import Session


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "identity"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)

    display_name: Mapped[str | None] = mapped_column(String(255))
    nickname: Mapped[str] = mapped_column(
        String(255), nullable=False, default=nickname_from_user
    )

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

    scripts: Mapped[list["Script"]] = relationship("Script", back_populates="user")

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
