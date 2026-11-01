from enum import Enum


class PlatformType(str, Enum):
    MACOS = "macos"
    WINDOWS = "windows"
    LINUX = "linux"
    IOS = "ios"
    ANDROID = "android"
    OTHER = "other"


class ClientDeviceStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
