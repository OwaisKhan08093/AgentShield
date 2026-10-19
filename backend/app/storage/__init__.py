"""Storage and persistence module for AgentShield."""

from app.storage.database import DatabaseManager
from app.storage.exceptions import (
    DuplicateRunError,
    RunNotFoundError,
    SchemaVersionError,
    StorageError,
    StorageIntegrityError,
)
from app.storage.repository import (
    EvaluationRepository,
    SQLiteEvaluationRepository,
    get_default_repository,
)
from app.storage.schema import (
    CURRENT_SCHEMA_VERSION,
    get_current_schema_version,
    initialize_schema,
)

__all__ = [
    "CURRENT_SCHEMA_VERSION",
    "DatabaseManager",
    "DuplicateRunError",
    "EvaluationRepository",
    "RunNotFoundError",
    "SQLiteEvaluationRepository",
    "SchemaVersionError",
    "StorageError",
    "StorageIntegrityError",
    "get_current_schema_version",
    "get_default_repository",
    "initialize_schema",
]
