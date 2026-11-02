from enum import Enum


class DeviceType(str, Enum):
    PHYSICAL = "physical"
    VIRTUAL = "virtual"
    VPS = "vps"
    CLOUD = "cloud"
    OTHER = "other"


class AuthenticationType(str, Enum):
    PASSWORD = "password"
    SSH_KEY = "ssh_key"
    AGENT = "agent"
    OTHER = "other"


class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ServiceType(str, Enum):
    SYSTEMD = "systemd"
    DOCKER = "docker"
    APPLICATION = "application"
    DATABASE = "database"
    WEB_SERVER = "web_server"
    OTHER = "other"


class ResourceStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    RESTARTING = "restarting"
    PAUSED = "paused"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ContainerStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    EXITED = "exited"
    DEAD = "dead"
    UNKNOWN = "unknown"


class DbmsType(str, Enum):
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MARIADB = "mariadb"
    MONGODB = "mongodb"
    REDIS = "redis"
    SQLITE = "sqlite"
    OTHER = "other"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NOT_VERIFIED = "not_verified"
