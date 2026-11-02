from enum import Enum


class SyncStatus(str, Enum):
    SYNCED = "synced"
    PENDING = "pending"
    SYNCING = "syncing"
    CONFLICT = "conflict"
    FAILED = "failed"
    OFFLINE = "offline"


class ChangeOperation(str, Enum):
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"
