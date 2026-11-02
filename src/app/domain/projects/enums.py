from enum import Enum


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class ProjectType(str, Enum):
    SOFTWARE = "software"
    INFRASTRUCTURE = "infrastructure"
    FULLSTACK = "fullstack"
    OTHER = "other"


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"
    LOCAL = "local"
    OTHER = "other"
