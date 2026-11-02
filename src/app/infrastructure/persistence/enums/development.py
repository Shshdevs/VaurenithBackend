from enum import Enum


class RepositoryType(str, Enum):
    GIT = "git"
    OTHER = "other"


class RepositoryStatus(str, Enum):
    CLEAN = "clean"
    MODIFIED = "modified"
    CONFLICTED = "conflicted"
    UNTRACKED = "untracked"
    UNKNOWN = "unknown"


class ComponentType(str, Enum):
    FILE = "file"
    DIRECTORY = "directory"
    MODULE = "module"
    PACKAGE = "package"
    CLASS = "class"
    FUNCTION = "function"
    INTERFACE = "interface"
    VARIABLE = "variable"
    SYMBOL = "symbol"
    OTHER = "other"


class DependencyType(str, Enum):
    IMPORT = "import"
    INHERITANCE = "inheritance"
    IMPLEMENTATION = "implementation"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"
    REFERENCE = "reference"
    CALL = "call"
    INCLUDE = "include"
    OTHER = "other"
