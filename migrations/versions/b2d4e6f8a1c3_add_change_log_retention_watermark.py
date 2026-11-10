from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2d4e6f8a1c3"
down_revision: str | None = "91e2a3b4c5d6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "change_log_retention",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("expired_through_sequence", sa.BigInteger(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["identity.users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        schema="synchronization",
    )


def downgrade() -> None:
    op.drop_table("change_log_retention", schema="synchronization")
