import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...base import Base

if TYPE_CHECKING:
    from .repository import Repository


class Branch(Base):
    __tablename__ = "branches"
    __table_args__ = (
        Index(
            "uq_branches_repository_id_name_is_remote",
            "repository_id",
            "name",
            "is_remote",
            unique=True,
        ),
        {"schema": "development"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "development.repositories.id", deferrable=True, initially="IMMEDIATE"
        ),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    commit_hash: Mapped[str | None] = mapped_column(String(64))
    is_remote: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
    last_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    repository: Mapped["Repository"] = relationship(
        "Repository", back_populates="branches", foreign_keys=[repository_id]
    )
