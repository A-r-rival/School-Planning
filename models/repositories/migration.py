# -*- coding: utf-8 -*-
"""
Database migration utilities
Handles schema migrations and table evolution
"""
import sqlite3
from typing import Callable, Iterable


class DatabaseMigration:
    """
    Manages database schema migrations.

    - Idempotent
    - Transaction-safe
    - Ordered
    """

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    # ---------- public API ----------

    def run_all(self) -> None:
        """Execute all migrations in order."""
        for migration in self._migrations():
            migration()

    # ---------- migrations registry ----------

    def _migrations(self) -> Iterable[Callable]:
        """
        Ordered list of migrations to execute.
        Add new migrations to the END of this list.
        """
        return [
            self._001_initial_schema,
            self._002_add_preferred_day_span_to_teachers,
        ]

    # ---------- helpers ----------

    def _column_exists(self, table: str, column: str) -> bool:
        """Check if a column exists in a table."""
        cursor = self._conn.execute(f"PRAGMA table_info({table})")
        return column in {row[1] for row in cursor.fetchall()}

    def _table_exists(self, table: str) -> bool:
        """Check if a table exists in the database."""
        cursor = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        return cursor.fetchone() is not None

    def _log(self, message: str) -> None:
        print(f"[MIGRATION] {message}")

    # ---------- actual migrations ----------
    
    def _001_initial_schema(self) -> None:
        """Create initial database schema (all tables and indexes)."""
        # Skip if already created
        if self._table_exists("Fakulteler"):
            return
        
        self._log("Creating initial schema (15 tables)")
        from .migrations.initial_schema_0001 import create_initial_schema
        create_initial_schema(self._conn)
        self._log("✅ Initial schema created")
    
    def _002_add_preferred_day_span_to_teachers(self) -> None:
        """
        Adds preferred_day_span column to Ogretmenler table.
        """
        if self._column_exists("Ogretmenler", "preferred_day_span"):
            return

        self._log("Adding preferred_day_span column to Ogretmenler")

        with self._conn:
            self._conn.execute(
                """
                ALTER TABLE Ogretmenler
                ADD COLUMN preferred_day_span INTEGER DEFAULT NULL
                """
            )

        self._log("✅ Ogretmenler migrated successfully")
