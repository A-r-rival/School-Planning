# -*- coding: utf-8 -*-
"""
TeacherRepository - Isolates teacher-related data operations
Normalized, title-aware, transaction-safe repository
"""
import sqlite3
from typing import List, Tuple, Optional


class TeacherRepository:
    """
    Repository for teacher data access.
    Transaction boundaries are managed by the caller.
    """

    _NAME_MATCH_SQL = "LOWER(TRIM(ad || ' ' || soyad)) = LOWER(TRIM(?))"

    # Titles without dots (compatible with rstrip)
    _TITLES = {"prof", "dr", "doç", "yard", "assoc", "asst", "yrd"}

    def __init__(self, cursor: sqlite3.Cursor, conn: sqlite3.Connection):
        self.c = cursor
        self.conn = conn

    # ---------- normalization helpers ----------

    def _strip_titles(self, parts: list[str]) -> list[str]:
        return [
            p for p in parts
            if p.rstrip(".") not in self._TITLES
        ]

    def _parse_name(self, full_name: str) -> Tuple[str, str]:
        """
        Parse full name into (ad, soyad), stripping academic titles.
        """
        parts = full_name.casefold().split()
        parts = self._strip_titles(parts)

        if not parts:
            return full_name.strip(), ""

        ad = parts[0].capitalize()
        soyad = " ".join(p.capitalize() for p in parts[1:])
        return ad, soyad

    def _normalize_full_name(self, full_name: str) -> str:
        """
        Normalize name exactly the way DB comparison expects it.
        Single source of truth.
        """
        ad, soyad = self._parse_name(full_name.strip())
        return f"{ad} {soyad}".strip()

    # ---------- public API ----------

    def get_or_create(self, full_name: str) -> int:
        normalized = self._normalize_full_name(full_name)

        self.c.execute(
            f"SELECT ogretmen_num FROM Ogretmenler WHERE {self._NAME_MATCH_SQL}",
            (normalized,)
        )
        row = self.c.fetchone()
        if row:
            return row[0]

        ad, soyad = self._parse_name(full_name)

        self.c.execute(
            "INSERT INTO Ogretmenler (ad, soyad, bolum_adi) VALUES (?, ?, ?)",
            (ad, soyad, "Genel")
        )
        return self.c.lastrowid

    def exists(self, full_name: str) -> bool:
        normalized = self._normalize_full_name(full_name)

        self.c.execute(
            f"SELECT 1 FROM Ogretmenler WHERE {self._NAME_MATCH_SQL}",
            (normalized,)
        )
        return self.c.fetchone() is not None

    def get_all(self) -> List[Tuple[int, str]]:
        self.c.execute(
            "SELECT ogretmen_num, ad || ' ' || soyad FROM Ogretmenler ORDER BY ad"
        )
        return self.c.fetchall()

    def get_by_id(self, teacher_id: int) -> Optional[Tuple[str, str]]:
        self.c.execute(
            "SELECT ad, soyad FROM Ogretmenler WHERE ogretmen_num = ?",
            (teacher_id,)
        )
        return self.c.fetchone()

    def update_department(self, teacher_id: int, department_name: str) -> bool:
        try:
            self.c.execute(
                "UPDATE Ogretmenler SET bolum_adi = ? WHERE ogretmen_num = ?",
                (department_name, teacher_id)
            )
            return self.c.rowcount > 0
        except Exception:
            return False
