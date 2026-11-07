from typing import Any
from uuid import UUID

from app.domain.common.slug import make_slug


def slug_from_name(context: Any) -> str:
    values = context.get_current_parameters()
    entity_id = values.get("id")
    fallback = f"item-{entity_id.hex[:8]}" if isinstance(entity_id, UUID) else "item"
    return make_slug(values.get("name") or "", fallback)


def nickname_from_user(context: Any) -> str:
    values = context.get_current_parameters()
    display_name = values.get("display_name")
    email = values.get("email") or ""
    source = display_name.strip() if isinstance(display_name, str) else ""
    source = source or email.partition("@")[0]
    entity_id = values.get("id")
    fallback = f"user-{entity_id.hex[:8]}" if isinstance(entity_id, UUID) else "user"
    return make_slug(source, fallback)
