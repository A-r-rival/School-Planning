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
        """
        Run all migrations in order.
        Safe to call multiple times.
        """
        for migration in self._migrations():
            migration()

    # ---------- migrations registry ----------

    def _migrations(self) -> Iterable[Callable[[], None]]:
        """
        Ordered list of migration steps.
        Add new migrations here.
        """
        return [
            self._add_preferred_day_span_to_teachers,
        ]

    # ---------- helpers ----------

    def _column_exists(self, table: str, column: str) -> bool:
        cursor = self._conn.execute(f"PRAGMA table_info({table})")
        return column in {row[1] for row in cursor.fetchall()}

    def _log(self, message: str) -> None:
        print(f"[MIGRATION] {message}")

    # ---------- actual migrations ----------

    def _add_preferred_day_span_to_teachers(self) -> None:
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
