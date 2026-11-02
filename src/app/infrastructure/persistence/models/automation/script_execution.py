import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...base import Base

if TYPE_CHECKING:
    from ..identity.client_device import (
        ClientDevice,
    )
    from ..infrastructure.device import Device
    from .script import Script

from ...enums.automation import ExecutionStatus


class ScriptExecution(Base):
    __tablename__ = "script_executions"
    __table_args__ = (
        Index("uq_script_executions_idempotency_key", "idempotency_key", unique=True),
        {"schema": "automation"},
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        nullable=False,
        server_default=text("gen_random_uuid()"),
    )
    script_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("automation.scripts.id", deferrable=True, initially="IMMEDIATE"),
        nullable=False,
    )
    device_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("infrastructure.devices.id", deferrable=True, initially="IMMEDIATE"),
    )
    client_device_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "identity.client_devices.id", deferrable=True, initially="IMMEDIATE"
        ),
        nullable=False,
    )
    parameters: Mapped[Any | None] = mapped_column(JSONB)
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(
            ExecutionStatus,
            name="execution_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        server_default=text("'pending'"),
    )
    exit_code: Mapped[int | None] = mapped_column(Integer)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    sanitized_output_summary: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )

    script: Mapped["Script"] = relationship(
        "Script", back_populates="script_executions", foreign_keys=[script_id]
    )

    device: Mapped["Device"] = relationship(
        "Device", back_populates="script_executions", foreign_keys=[device_id]
    )

    client_device: Mapped["ClientDevice"] = relationship(
        "ClientDevice",
        back_populates="script_executions",
        foreign_keys=[client_device_id],
    )
