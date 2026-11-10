class NotFound(Exception):
    pass


class Unauthorized(Exception):
    pass


class Conflict(Exception):
    pass


class InvalidInput(Exception):
    pass


class ChangeLogCursorExpired(Exception):
    def __init__(self, restart_sequence: int) -> None:
        self.restart_sequence = restart_sequence
        super().__init__("Change log cursor expired; a full synchronization is required")
