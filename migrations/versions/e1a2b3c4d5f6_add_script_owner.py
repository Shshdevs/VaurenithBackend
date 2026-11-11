from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e1a2b3c4d5f6"
down_revision: str | None = "d6e8f1a2b3c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "scripts",
        sa.Column("user_id", sa.UUID(), nullable=True),
        schema="automation",
    )
    op.create_foreign_key(
        "fk_scripts_user_id_users",
        "scripts",
        "users",
        ["user_id"],
        ["id"],
        source_schema="automation",
        referent_schema="identity",
        deferrable=True,
        initially="IMMEDIATE",
    )
    op.create_index(
        "ix_scripts_user_id",
        "scripts",
        ["user_id"],
        schema="automation",
    )


def downgrade() -> None:
    op.drop_index("ix_scripts_user_id", table_name="scripts", schema="automation")
    op.drop_constraint(
        "fk_scripts_user_id_users", "scripts", schema="automation", type_="foreignkey"
    )
    op.drop_column("scripts", "user_id", schema="automation")
