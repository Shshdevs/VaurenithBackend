from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.application.common.exceptions import InvalidInput
from app.application.common.transactional import transactional
from app.application.common.unit_of_work import UnitOfWork
from app.application.identity import VerifiedIdentity
from app.application.infrastructure.exceptions import DeviceNotFound
from app.application.infrastructure.interfaces import DeviceRepository
from app.application.monitoring.dto import EventData
from app.application.monitoring.exceptions import EventClientDeviceNotFound
from app.application.monitoring.interfaces import EventRepository
from app.application.projects.exceptions import ProjectNotFound
from app.application.projects.interfaces import ProjectRepository
from app.domain.monitoring import Event, EventResult, EventType, InvalidEvent

_SECRET_KEY_PARTS = (
    "password",
    "secret",
    "token",
    "credential",
    "authorization",
    "privatekey",
    "apikey",
)


def _contains_secret_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = "".join(
                character for character in str(key).lower() if character.isalnum()
            )
            if any(part in normalized for part in _SECRET_KEY_PARTS):
                return True
            if _contains_secret_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_secret_key(nested) for nested in value)
    return False


class CreateEvent:
    def __init__(
        self,
        event_repository: EventRepository,
        device_repository: DeviceRepository,
        project_repository: ProjectRepository,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._event_repository = event_repository
        self._device_repository = device_repository
        self._project_repository = project_repository
        self._unit_of_work = unit_of_work

    @transactional
    async def create_event(
        self,
        identity: VerifiedIdentity,
        event_type: EventType,
        result: EventResult,
        created_at: datetime,
        project_id: UUID | None,
        device_id: UUID | None,
        description: str | None,
        metadata: dict[str, Any] | None,
        client_device_id: UUID | None,
    ) -> EventData:
        if (
            project_id is not None
            and await self._project_repository.get_by_id(identity.user_id, project_id)
            is None
        ):
            raise ProjectNotFound(str(project_id))
        if (
            device_id is not None
            and await self._device_repository.get_by_id(identity, device_id) is None
        ):
            raise DeviceNotFound(str(device_id))
        if (
            client_device_id is not None
            and not await self._event_repository.owns_client_device(
                identity.user_id, client_device_id
            )
        ):
            raise EventClientDeviceNotFound(str(client_device_id))
        if _contains_secret_key(metadata):
            raise InvalidInput("Event metadata must not contain secret fields")
        try:
            event = Event(
                event_id=uuid4(),
                user_id=identity.user_id,
                event_type=EventType(event_type),
                result=EventResult(result),
                created_at=created_at,
                project_id=project_id,
                device_id=device_id,
                description=description,
                metadata=metadata,
                client_device_id=client_device_id,
            )
        except (InvalidEvent, ValueError) as error:
            raise InvalidInput(str(error)) from error
        await self._event_repository.create(event)
        return EventData.from_event(event)
