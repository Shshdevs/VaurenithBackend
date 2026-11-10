from typing import Literal

from app.api.schemas.common import Schema


class ChangeLogResyncRequired(Schema):
    resync_required: Literal[True] = True
    restart_sequence: int
