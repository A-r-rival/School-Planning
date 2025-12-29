# -*- coding: utf-8 -*-
"""
ScheduleRepository - Manages schedule data operations
DRY SQL, optimized conflict detection, clean entity mapping
"""
import sqlite3
from typing import List, Optional
from models.entities import ScheduleSlot, ScheduledCourse


class ScheduleRepository:
    """
    Repository for schedule data access.
    Transaction boundaries managed by caller.
    """

    # DRY: Base SELECT used by multiple queries
    _BASE_SELECT = """
        SELECT 
            dp.program_id,
            d.ders_adi,
            dp.ders_instance,
            d.ders_kodu,
            o.ad || ' ' || o.soyad AS hoca,
            dp.gun,
            dp.baslangic,
            dp.bitis,
            dp.siniflar,
            GROUP_CONCAT(DISTINCT dhi.havuz_kodu) AS havuz_kodlari
        FROM Ders_Programi dp
        JOIN Dersler d ON dp.ders_id = d.ders_id AND dp.ders_instance = d.ders_instance
        JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
        LEFT JOIN Ders_Havuz_Iliskisi dhi ON d.ders_id = dhi.ders_id
    """

    def __init__(self, cursor: sqlite3.Cursor, conn: sqlite3.Connection):
        self.c = cursor
        self.conn = conn

    # ---------- conflict detection ----------

    def has_conflict(self, slot: ScheduleSlot, exclude_id: Optional[int] = None) -> bool:
        """
        Check if a time slot conflicts with existing schedule.
        SQL-level optimization: O(1) instead of O(n) Python loop.
        
        Args:
            slot: ScheduleSlot to check
            exclude_id: Optional program_id to exclude (for updates)
        
        Returns:
            bool: True if conflict exists
        """
        query = """
            SELECT 1 FROM Ders_Programi
            WHERE gun = ?
            AND baslangic < ?
            AND bitis > ?
        """
        params = [
            slot.day,
            slot.end_str,
            slot.start_str,
        ]

        if exclude_id is not None:
            query += " AND program_id != ?"
            params.append(exclude_id)

        query += " LIMIT 1"
        
        self.c.execute(query, params)
        return self.c.fetchone() is not None

    # ---------- CRUD operations ----------

    def add(
        self,
        ders_id: int,
        ders_instance: int,
        ogretmen_id: int,
        slot: ScheduleSlot,
        siniflar: str = ""
    ) -> int:
        """
        Add a course to the schedule.
        
        Args:
            ders_id: Course ID from Dersler table
            ders_instance: Course instance number
            ogretmen_id: Teacher ID
            slot: ScheduleSlot with day/time
            siniflar: Optional class list
        
        Returns:
            int: program_id of inserted record
        """
        gun, baslangic, bitis = slot.to_db_tuple()
        
        self.c.execute(
            """
            INSERT INTO Ders_Programi (
                ders_id, ders_instance, ogretmen_id, gun, baslangic, bitis, siniflar
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (ders_id, ders_instance, ogretmen_id, gun, baslangic, bitis, siniflar)
        )
        return self.c.lastrowid

    def remove_by_id(self, program_id: int) -> bool:
        """Remove a schedule entry by ID."""
        self.c.execute("DELETE FROM Ders_Programi WHERE program_id = ?", (program_id,))
        return self.c.rowcount > 0

    def get_by_id(self, program_id: int) -> Optional[ScheduledCourse]:
        """Get full course details by program_id."""
        self.c.execute(
            self._BASE_SELECT + " WHERE dp.program_id = ? GROUP BY dp.program_id",
            (program_id,)
        )
        row = self.c.fetchone()
        return self._row_to_entity(row) if row else None

    def get_all(self) -> List[ScheduledCourse]:
        """Get all scheduled courses."""
        self.c.execute(
            self._BASE_SELECT + " GROUP BY dp.program_id ORDER BY dp.gun, dp.baslangic"
        )
        return [self._row_to_entity(row) for row in self.c.fetchall()]

    def get_by_teacher(self, teacher_id: int) -> List[ScheduledCourse]:
        """Get schedule for specific teacher."""
        self.c.execute(
            self._BASE_SELECT + """
                WHERE dp.ogretmen_id = ?
                GROUP BY dp.program_id
                ORDER BY dp.gun, dp.baslangic
            """,
            (teacher_id,)
        )
        return [self._row_to_entity(row) for row in self.c.fetchall()]

    # ---------- helpers ----------

    @staticmethod
    def _row_to_entity(row: tuple) -> ScheduledCourse:
        """Map database row to ScheduledCourse entity."""
        return ScheduledCourse(
            program_id=row[0],
            ders_adi=row[1],
            ders_instance=row[2],
            ders_kodu=row[3],
            hoca=row[4],
            gun=row[5],
            baslangic=row[6],
            bitis=row[7],
            siniflar=row[8],
            havuz_kodlari=row[9],
        )
