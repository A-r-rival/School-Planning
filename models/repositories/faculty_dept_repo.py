# -*- coding: utf-8 -*-
"""
FacultyDepartmentRepository - Isolates faculty and department data operations
"""
import sqlite3
from typing import List, Tuple, Dict, Optional

class FacultyDepartmentRepository:
    """
    Repository for faculty and department data access.
    """
    def __init__(self, cursor: sqlite3.Cursor, conn: sqlite3.Connection):
        self.c = cursor
        self.conn = conn

    def get_faculties(self) -> List[Tuple[int, str]]:
        """Get all faculties."""
        self.c.execute("SELECT fakulte_num, fakulte_adi FROM Fakulteler ORDER BY fakulte_adi")
        return self.c.fetchall()

    def get_departments_by_faculty(self, faculty_id: int) -> List[Tuple[int, str]]:
        """Get departments for a specific faculty."""
        self.c.execute("""
            SELECT bolum_id, bolum_adi
            FROM Bolumler
            WHERE fakulte_num = ?
            ORDER BY bolum_adi
        """, (faculty_id,))
        return self.c.fetchall()

    def get_all_departments(self) -> List[tuple]:
        """Get all departments. Returns (bolum_id, bolum_adi, fakulte_adi)"""
        self.c.execute("""
            SELECT b.bolum_id, b.bolum_adi, f.fakulte_adi 
            FROM Bolumler b
            JOIN Fakulteler f ON b.fakulte_num = f.fakulte_num
            ORDER BY f.fakulte_adi, b.bolum_adi
        """)
        return self.c.fetchall()

    def add_faculty(self, faculty_name: str) -> Optional[int]:
        """Add a new faculty, returns ID or None if exists."""
        try:
            # Check if exists
            self.c.execute("SELECT fakulte_num FROM Fakulteler WHERE fakulte_adi = ?", (faculty_name,))
            existing = self.c.fetchone()
            if existing:
                return existing[0]
                
            self.c.execute("INSERT INTO Fakulteler (fakulte_adi) VALUES (?)", (faculty_name,))
            return self.c.lastrowid
        except Exception as e:
            print(f"Error adding faculty: {e}")
            return None

    def add_department(self, faculty_id: int, department_name: str) -> Optional[int]:
        """Add a new department, returns ID or None if exists."""
        try:
            # Check if exists
            self.c.execute("SELECT bolum_id FROM Bolumler WHERE fakulte_num = ? AND bolum_adi = ?", 
                          (faculty_id, department_name))
            existing = self.c.fetchone()
            if existing:
                return existing[0]
                
            self.c.execute("INSERT INTO Bolumler (fakulte_num, bolum_adi) VALUES (?, ?)", 
                          (faculty_id, department_name))
            return self.c.lastrowid
        except Exception as e:
            print(f"Error adding department: {e}")
            return None

    def fakulte_numarasini_al(self, ogrenci_num2: int) -> int:
        self.c.execute('SELECT fakulte_num FROM Ogrenciler WHERE ogrenci_num = ?', (ogrenci_num2,))
        result = self.c.fetchone()
        return result[0] if result else None

    def bolum_numarasini_al(self, bolum_adi: str, fakulte_num: int) -> int:
        self.c.execute('SELECT bolum_id FROM Bolumler WHERE bolum_adi = ? AND fakulte_num = ?', (bolum_adi, fakulte_num))
        result = self.c.fetchone()
        return result[0] if result else None

    def get_department_name(self, dept_id: int) -> Optional[str]:
        """Get department name by its ID."""
        self.c.execute('SELECT bolum_adi FROM Bolumler WHERE bolum_id = ?', (dept_id,))
        res = self.c.fetchone()
        return res[0] if res else None
