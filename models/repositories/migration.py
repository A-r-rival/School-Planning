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
            self._003_add_teacher_course_preferences,
            self._004_add_curriculum_indexes,
            self._005_add_unavailability_description,
            self._006_add_schedule_columns,
            self._007_add_teacher_room_preferences,
            self._008_add_schedule_snapshots_table,
            self._009_add_room_notes,
            self._010_add_common_course_groups,
        ]

    def _009_add_room_notes(self) -> None:
        """Adds notlar column to Derslikler table."""
        from .migrations.migration_009_add_room_notes import up
        up(self._conn)

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

    def _003_add_teacher_course_preferences(self) -> None:
        """
        Creates Ogretmen_Ders_Tercihleri table.
        """
        if self._table_exists("Ogretmen_Ders_Tercihleri"):
            return

        self._log("Creating Ogretmen_Ders_Tercihleri table")
        from .migrations.teacher_course_preferences_003 import up as create_teacher_course_preferences_table
        create_teacher_course_preferences_table(self._conn)
        self._log("✅ Ogretmen_Ders_Tercihleri table created")

    def _004_add_curriculum_indexes(self) -> None:
        """
        Adds indexes for Curriculum View performance.
        idx_dersler_kodu, idx_dhi_bolum, idx_dhi_havuz
        """
        self._log("Adding curriculum view indexes...")
        from .migrations.migration_004_curriculum_indexes import up as add_curriculum_indexes
        add_curriculum_indexes(self._conn)
        self._log("✅ Curriculum indexes created")

    def _005_add_unavailability_description(self) -> None:
        """
        Adds description column to Ogretmen_Musaitlik table.
        """
        from .migrations.migration_005_add_unavailability_description import add_description_to_unavailability
        add_description_to_unavailability(self._conn)

    def _006_add_schedule_columns(self) -> None:
        """
        Adds derslik_id and ders_tipi to Ders_Programi.
        """
        from .migrations.migration_006_add_schedule_columns import up as add_schedule_columns
        add_schedule_columns(self._conn)

    def _007_add_teacher_room_preferences(self) -> None:
        """
        Adds room_request column to Ogretmenler table
        """
        if self._column_exists("Ogretmenler", "room_request"):
            return

        from .migrations.migration_007_add_teacher_room_preferences import up as add_room_preferences
        add_room_preferences(self._conn)

    def _008_add_schedule_snapshots_table(self) -> None:
        """
        Creates schedule_snapshots table.
        """
        if self._table_exists("schedule_snapshots"):
            return

        self._log("Creating schedule_snapshots table")
        from models.repositories.migrations.migration_008_schedule_snapshots import create_schedule_snapshots_table
        create_schedule_snapshots_table(self._conn)
        self._log("✅ schedule_snapshots table created")

    def _010_add_common_course_groups(self) -> None:
        """
        Creates Ortak_Ders_Gruplari table.
        """
        if self._table_exists("Ortak_Ders_Gruplari"):
            return

        self._log("Creating Ortak_Ders_Gruplari table")
        from .migrations.migration_010_common_course_groups import up
        up(self._conn)
        self._log("✅ Ortak_Ders_Gruplari table created")
