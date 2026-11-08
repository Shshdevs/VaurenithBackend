from datetime import datetime

from app.domain.common.entity import Entity
from app.domain.common.slug import make_slug
from app.domain.common.types import EntityId
from app.domain.identity.value_objects.email import EmailAddress


class User(Entity):
    """Registered cloud users"""

    def __init__(
        self,
        entity_id: EntityId,
        email: EmailAddress,
        display_name: str | None,
        auth_provider: str | None,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(entity_id)
        self._email = email
        self._display_name = display_name
        self._auth_provider = auth_provider
        self._created_at = created_at
        self._updated_at = updated_at

    @property
    def email(self) -> EmailAddress:
        return self._email

    @property
    def display_name(self) -> str | None:
        return self._display_name

    @property
    def nickname(self) -> str:
        source = (self._display_name or "").strip() or self._email.value.partition("@")[0]
        return make_slug(source, f"user-{self.id.hex[:8]}")

    @property
    def auth_provider(self) -> str | None:
        return self._auth_provider

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
