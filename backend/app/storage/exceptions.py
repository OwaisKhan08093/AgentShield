"""Exceptions for AgentShield storage and persistence layer."""


class StorageError(Exception):
    """Base exception for all storage and database errors."""


class DuplicateRunError(StorageError):
    """Raised when attempting to save a run ID that already exists without allow_overwrite."""


class RunNotFoundError(StorageError):
    """Raised when an evaluation run ID does not exist in storage."""


class StorageIntegrityError(StorageError):
    """Raised when database constraints or schema verification fails."""


class SchemaVersionError(StorageError):
    """Raised when database schema version is incompatible."""
