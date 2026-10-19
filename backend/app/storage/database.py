"""SQLite database connection and session management."""

import logging
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union

from app.storage.exceptions import StorageError
from app.storage.schema import initialize_schema

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite connections, transactions, and schema initialization."""

    def __init__(self, database_path: Union[str, Path] = "agentshield.db"):
        """Initialize the database manager with a file path or ':memory:'.

        Args:
            database_path: File system path or ':memory:' for transient in-memory database.
        """
        self.database_path_raw = str(database_path)
        self.is_memory = self.database_path_raw == ":memory:"

        if self.is_memory:
            self.database_path = ":memory:"
            # Retain a persistent connection for in-memory databases so state survives across calls
            self._memory_conn: Optional[sqlite3.Connection] = None
        else:
            resolved = Path(self.database_path_raw).expanduser().resolve()
            self.database_path = str(resolved)
            # Ensure parent directory exists
            resolved.parent.mkdir(parents=True, exist_ok=True)
            self._memory_conn = None

        self._initialized = False

    def get_connection(self) -> sqlite3.Connection:
        """Create and configure a SQLite connection with foreign keys and WAL mode.

        Returns:
            sqlite3.Connection configured with sqlite3.Row factory and enabled foreign keys.
        """
        if self.is_memory:
            if self._memory_conn is None:
                self._memory_conn = sqlite3.connect(
                    ":memory:",
                    check_same_thread=False,
                )
                self._configure_connection(self._memory_conn, is_memory=True)
            return self._memory_conn

        try:
            conn = sqlite3.connect(
                self.database_path,
                timeout=10.0,
                check_same_thread=False,
            )
            self._configure_connection(conn, is_memory=False)
            return conn
        except sqlite3.Error as e:
            logger.error("Failed to connect to SQLite database at %s: %s", self.database_path, e)
            raise StorageError(f"Failed to connect to database: {e}") from e

    def _configure_connection(self, conn: sqlite3.Connection, is_memory: bool = False) -> None:
        """Apply necessary PRAGMAs and row factory to connection."""
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA busy_timeout = 5000;")
        if not is_memory:
            try:
                cursor.execute("PRAGMA journal_mode = WAL;")
            except sqlite3.Error:
                # WAL mode may fail on some read-only or network filesystems; fallback gracefully
                pass

    @contextmanager
    def connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding a database connection.

        For file-based databases, closes the connection upon exit.
        """
        conn = self.get_connection()
        try:
            yield conn
        finally:
            if not self.is_memory:
                conn.close()

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding a connection within an atomic transaction.

        Automatically commits on successful block exit, and rolls back on exception.
        """
        conn = self.get_connection()
        try:
            with conn:
                yield conn
        except Exception as e:
            logger.error("Transaction rolled back due to error: %s", e)
            raise
        finally:
            if not self.is_memory:
                conn.close()

    def initialize(self) -> None:
        """Idempotently initialize schema and tables."""
        with self.connection() as conn:
            initialize_schema(conn)
        self._initialized = True

    def close(self) -> None:
        """Close any persistent connection (such as for :memory: databases)."""
        if self.is_memory and self._memory_conn is not None:
            self._memory_conn.close()
            self._memory_conn = None
