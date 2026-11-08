import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.persistence.base import Base
from app.infrastructure.persistence.slug_defaults import slug_from_name

if TYPE_CHECKING:
    from app.infrastructure.persistence.models.development.branch import Branch
    from app.infrastructure.persistence.models.development.code_component import (
        CodeComponent,
    )
    from app.infrastructure.persistence.models.development.commit import Commit
    from app.infrastructure.persistence.models.projects.project import Project

from app.domain.development.enums import RepositoryType


class Repository(Base):
    __tablename__ = "repositories"
    __table_args__ = {"schema": "development"}

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.projects.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, default=slug_from_name)
    description: Mapped[str | None] = mapped_column(Text)
    remote_url: Mapped[str | None] = mapped_column(Text)
    default_branch: Mapped[str | None] = mapped_column(String(255))
    repository_type: Mapped[RepositoryType] = mapped_column(
        Enum(
            RepositoryType,
            name="repository_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'git'"),
    )
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

    project: Mapped["Project"] = relationship(
        "Project", back_populates="repositories", foreign_keys=[project_id]
    )

    branches: Mapped[list["Branch"]] = relationship(
        "Branch", back_populates="repository", foreign_keys="Branch.repository_id"
    )

    commits: Mapped[list["Commit"]] = relationship(
        "Commit", back_populates="repository", foreign_keys="Commit.repository_id"
    )

    code_components: Mapped[list["CodeComponent"]] = relationship(
        "CodeComponent",
        back_populates="repository",
        foreign_keys="CodeComponent.repository_id",
    )
