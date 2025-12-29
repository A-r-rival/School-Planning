# -*- coding: utf-8 -*-
"""
CourseRepository - Manages course data operations
Type-safe, minimal, transaction-agnostic
"""
import sqlite3
from typing import List, NamedTuple, Optional


# ---------- DTOs ----------

class CourseInstance(NamedTuple):
    """Represents a course instance (section)."""
    instance: int
    code: str


class CourseLookupResult(NamedTuple):
    """Result of get_or_create lookup."""
    instance: int
    code: str
    exists: bool  # False means caller must create via ders_ekle


# ---------- Repository ----------

class CourseRepository:
    """
    Repository for course data access.
    
    NOTE:
    This repository does NOT commit transactions.
    Transaction boundaries are managed by the calling service/model.
    """

    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    # ---------- Queries ----------

    def get_or_create(self, name: str, default_code: str = "CODE") -> CourseLookupResult:
        """
        Get an existing course instance or signal that creation is required.

        Args:
            name: Course name
            default_code: Default code if not found
        
        Returns:
            CourseLookupResult with exists=False if caller must create

        Example:
            >>> result = repo.get_or_create("Matematik", "MAT101")
            >>> if not result.exists:
            ...     instance = model.ders_ekle(name, result.code, ...)
        """
        rows = self._fetch_instances(name)

        if rows:
            instance, code = rows[0]
            return CourseLookupResult(instance, code or default_code, True)

        return CourseLookupResult(1, default_code, False)

    def get_all(self) -> List[tuple[str, str]]:
        """Return all distinct courses (name, code)."""
        return self._execute(
            """
            SELECT DISTINCT ders_adi, ders_kodu
            FROM Dersler
            ORDER BY ders_adi
            """
        ).fetchall()

    def exists(self, name: str) -> bool:
        """Check if a course exists by name."""
        return self._execute(
            "SELECT 1 FROM Dersler WHERE ders_adi = ? LIMIT 1",
            (name,)
        ).fetchone() is not None

    def get_by_name(self, name: str) -> Optional[tuple[int, str, str]]:
        """Get single course by name: (ders_id, ders_adi, ders_kodu)."""
        return self._execute(
            """
            SELECT ders_id, ders_adi, ders_kodu
            FROM Dersler
            WHERE ders_adi = ?
            LIMIT 1
            """,
            (name,)
        ).fetchone()

    def get_instances(self, name: str) -> List[CourseInstance]:
        """Get all instances (sections) of a course."""
        rows = self._fetch_instances(name)
        return [CourseInstance(inst, code) for inst, code in rows]

    def get_id(self, name: str, instance: int) -> int:
        """
        Get course database ID by name and instance.
        
        Args:
            name: Course name
            instance: Course instance number
        
        Returns:
            ders_id from Dersler table
        
        Raises:
            CourseCreationError: Course instance not found
        """
        row = self._execute(
            """
            SELECT ders_id
            FROM Dersler
            WHERE ders_adi = ? AND ders_instance = ?
            """,
            (name, instance)
        ).fetchone()
        
        if not row:
            from models.services.exceptions import CourseCreationError
            raise CourseCreationError(
                f"Course instance not found: {name} (instance {instance})"
            )
        
        return row[0]
    
    def create_instance(self, name: str, code: str) -> int:
        """
        Create a new course instance with auto-calculated instance number.
        
        Args:
            name: Course name
            code: Course code
        
        Returns:
            int: New instance number
        
        Note: Properly calculates next instance to avoid conflicts.
        """
        # Calculate next instance number
        row = self._execute(
            """
            SELECT MAX(ders_instance)
            FROM Dersler
            WHERE ders_adi = ?
            """,
            (name,)
        ).fetchone()
        
        next_instance = (row[0] or 0) + 1
        
        # Create new instance
        self._execute(
            """
            INSERT INTO Dersler (ders_adi, ders_instance, ders_kodu)
            VALUES (?, ?, ?)
            """,
            (name, next_instance, code)
        )
        
        return next_instance

    # ---------- Internal helpers ----------

    def _execute(self, sql: str, params: tuple = ()):
        """
        Single point for SQL execution.
        Future: add logging, timing, debug here.
        """
        self._cursor.execute(sql, params)
        return self._cursor

    def _fetch_instances(self, name: str) -> List[tuple[int, str]]:
        """Helper to fetch course instances with consistent ordering."""
        return self._execute(
            """
            SELECT ders_instance, ders_kodu
            FROM Dersler
            WHERE ders_adi = ?
            ORDER BY ders_instance
            """,
            (name,)
        ).fetchall()
