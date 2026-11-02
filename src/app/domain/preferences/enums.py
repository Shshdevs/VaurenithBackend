from enum import Enum


class SettingScope(str, Enum):
    GLOBAL = "global"
    CLIENT = "client"
