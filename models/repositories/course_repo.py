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
