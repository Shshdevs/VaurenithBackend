from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.domain.common.slug import make_slug

revision: str = "78c4f3a6d219"
down_revision: str | None = "c24abab68356"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


SLUG_COLUMNS = (
    ("identity", "client_devices", "name", "slug", "device"),
    ("projects", "projects", "name", "slug", "project"),
    ("projects", "environments", "name", "slug", "environment"),
    ("infrastructure", "devices", "name", "slug", "device"),
    ("infrastructure", "device_groups", "name", "slug", "group"),
    ("infrastructure", "connections", "name", "slug", "connection"),
    ("infrastructure", "services", "name", "slug", "service"),
    ("infrastructure", "containers", "name", "slug", "container"),
    ("infrastructure", "databases", "name", "slug", "database"),
    ("development", "repositories", "name", "slug", "repository"),
    ("automation", "scripts", "name", "slug", "script"),
)


def _backfill_slug(
    schema: str,
    table: str,
    source_column: str,
    target_column: str,
    fallback_prefix: str,
) -> None:
    connection = op.get_bind()
    table_model = sa.Table(
        table, sa.MetaData(), schema=schema, autoload_with=connection
    )
    rows = connection.execute(
        sa.select(table_model.c.id, table_model.c[source_column])
    ).mappings()

    for row in rows:
        suffix = str(row["id"]).replace("-", "")[:8]
        slug = make_slug(row[source_column] or "", f"{fallback_prefix}-{suffix}")
        connection.execute(
            sa.update(table_model)
            .where(table_model.c.id == row["id"])
            .values({target_column: slug})
        )


def _backfill_nickname() -> None:
    connection = op.get_bind()
    user_table = sa.Table(
        "users", sa.MetaData(), schema="identity", autoload_with=connection
    )
    rows = connection.execute(
        sa.select(user_table.c.id, user_table.c.email, user_table.c.display_name)
    ).mappings()

    for row in rows:
        suffix = str(row["id"]).replace("-", "")[:8]
        display_name = (row["display_name"] or "").strip()
        source = display_name or row["email"].partition("@")[0]
        nickname = make_slug(source, f"user-{suffix}")
        connection.execute(
            sa.update(user_table)
            .where(user_table.c.id == row["id"])
            .values(nickname=nickname)
        )


def upgrade() -> None:
    for schema, table, _, target_column, _ in SLUG_COLUMNS:
        op.add_column(
            table,
            sa.Column(target_column, sa.String(length=255), nullable=True),
            schema=schema,
        )

    op.add_column(
        "users",
        sa.Column("nickname", sa.String(length=255), nullable=True),
        schema="identity",
    )

    for schema, table, source_column, target_column, fallback_prefix in SLUG_COLUMNS:
        _backfill_slug(schema, table, source_column, target_column, fallback_prefix)

    _backfill_nickname()

    for schema, table, _, target_column, _ in SLUG_COLUMNS:
        op.alter_column(
            table,
            target_column,
            existing_type=sa.String(length=255),
            nullable=False,
            schema=schema,
        )

    op.alter_column(
        "users",
        "nickname",
        existing_type=sa.String(length=255),
        nullable=False,
        schema="identity",
    )


def downgrade() -> None:
    op.drop_column("users", "nickname", schema="identity")
    for schema, table, _, target_column, _ in reversed(SLUG_COLUMNS):
        op.drop_column(table, target_column, schema=schema)
