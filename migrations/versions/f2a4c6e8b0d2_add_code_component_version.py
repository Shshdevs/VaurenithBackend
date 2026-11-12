"""add code component version"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2a4c6e8b0d2"
down_revision: str | None = "e1a2b3c4d5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "code_components",
        sa.Column("version", sa.BigInteger(), server_default=sa.text("1"), nullable=False),
        schema="development",
    )


def downgrade() -> None:
    op.drop_column("code_components", "version", schema="development")
