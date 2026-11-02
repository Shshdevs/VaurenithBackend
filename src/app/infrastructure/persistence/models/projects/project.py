import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...base import Base

if TYPE_CHECKING:
    from ..automation.script import Script
    from ..development.repository import Repository
    from ..identity.user import User
    from ..infrastructure.container import Container
    from ..infrastructure.database import Database
    from ..infrastructure.service import Service
    from ..monitoring.event import Event
    from ..monitoring.logs_metadata import (
        LogsMetadata,
    )
    from .environment import Environment
    from .project_device import (
        ProjectDevice,
    )

from .....domain.projects.enums import ProjectStatus, ProjectType


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = {"schema": "projects"}

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
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(
            ProjectType,
            name="project_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'other'"),
    )
    status: Mapped[ProjectStatus] = mapped_column(
        Enum(
            ProjectStatus,
            name="project_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'active'"),
    )
    metadata_: Mapped[Any | None] = mapped_column("metadata", JSONB)
    version: Mapped[int] = mapped_column(
        BigInteger, nullable=False, server_default=text("1")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(
        "User", back_populates="projects", foreign_keys=[user_id]
    )

    environments: Mapped[list["Environment"]] = relationship(
        "Environment", back_populates="project", foreign_keys="Environment.project_id"
    )

    project_devices: Mapped[list["ProjectDevice"]] = relationship(
        "ProjectDevice",
        back_populates="project",
        foreign_keys="ProjectDevice.project_id",
    )

    services: Mapped[list["Service"]] = relationship(
        "Service", back_populates="project", foreign_keys="Service.project_id"
    )

    containers: Mapped[list["Container"]] = relationship(
        "Container", back_populates="project", foreign_keys="Container.project_id"
    )

    databases: Mapped[list["Database"]] = relationship(
        "Database", back_populates="project", foreign_keys="Database.project_id"
    )

    repositories: Mapped[list["Repository"]] = relationship(
        "Repository", back_populates="project", foreign_keys="Repository.project_id"
    )

    scripts: Mapped[list["Script"]] = relationship(
        "Script", back_populates="project", foreign_keys="Script.project_id"
    )

    events: Mapped[list["Event"]] = relationship(
        "Event", back_populates="project", foreign_keys="Event.project_id"
    )

    logs_metadata: Mapped[list["LogsMetadata"]] = relationship(
        "LogsMetadata", back_populates="project", foreign_keys="LogsMetadata.project_id"
    )
