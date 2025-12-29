# -*- coding: utf-8 -*-
"""
TeacherRepository - Isolates teacher-related data operations
Implements professional review feedback: normalized name comparison
"""
from typing import List, Tuple, Optional


class TeacherRepository:
    """
    Repository for teacher data access.
    Encapsulates all teacher-related SQL operations.
    """
    
    def __init__(self, cursor, conn):
        """
        Initialize repository with database connection.
        
        Args:
            cursor: SQLite cursor object
            conn: SQLite connection object
        """
        self.c = cursor
        self.conn = conn
    
    def get_or_create(self, full_name: str) -> int:
        """
        Get teacher ID by name, or create if not exists.
        Uses normalized comparison (LOWER + TRIM) for reliability.
        
        Args:
            full_name: Teacher's full name (e.g., "Prof. Dr. Ali Yılmaz")
        
        Returns:
            int: Teacher ID (ogretmen_num)
        
        Example:
            >>> teacher_id = repo.get_or_create("Prof. Dr. Ali Yılmaz")
            >>> # If exists, returns existing ID
            >>> # If not, creates new teacher and returns new ID
        """
        # Normalize input
        normalized_name = full_name.strip()
        
        # Find by normalized name comparison (professional review feedback)
        self.c.execute(
            "SELECT ogretmen_num FROM Ogretmenler WHERE LOWER(TRIM(ad || ' ' || soyad)) = LOWER(TRIM(?))",
            (normalized_name,)
        )
        row = self.c.fetchone()
        if row:
            return row[0]

        # Parse name (simple split: first word = ad, rest = soyad)
        parts = normalized_name.split()
        ad = parts[0]
        soyad = ' '.join(parts[1:]) if len(parts) > 1 else ''

        # Create new teacher
        self.c.execute(
            "INSERT INTO Ogretmenler (ad, soyad, bolum_adi) VALUES (?, ?, ?)",
            (ad, soyad, "Genel")
        )
        return self.c.lastrowid

    def get_all(self) -> List[Tuple[int, str]]:
        """
        Get all teachers with their IDs.
        
        Returns:
            List of tuples: [(teacher_id, full_name), ...]
        
        Example:
            >>> teachers = repo.get_all()
            >>> # [(1, 'Prof. Dr. Ali'), (2, 'Dr. Mehmet'), ...]
        """
        self.c.execute("SELECT ogretmen_num, ad || ' ' || soyad FROM Ogretmenler ORDER BY ad")
        return self.c.fetchall()
    
    def get_by_id(self, teacher_id: int) -> Optional[Tuple[str, str]]:
        """
        Get teacher details by ID.
        
        Args:
            teacher_id: Teacher's database ID
        
        Returns:
            Tuple of (ad, soyad) or None if not found
        """
        self.c.execute("SELECT ad, soyad FROM Ogretmenler WHERE ogretmen_num = ?", (teacher_id,))
        row = self.c.fetchone()
        return row if row else None
    
    def exists(self, full_name: str) -> bool:
        """
        Check if a teacher exists by name.
        
        Args:
            full_name: Teacher's full name
        
        Returns:
            bool: True if teacher exists, False otherwise
        """
        self.c.execute(
            "SELECT 1 FROM Ogretmenler WHERE LOWER(TRIM(ad || ' ' || soyad)) = LOWER(TRIM(?))",
            (full_name.strip(),)
        )
        return self.c.fetchone() is not None
    
    def update_department(self, teacher_id: int, department_name: str) -> bool:
        """
        Update teacher's department.
        
        Args:
            teacher_id: Teacher's database ID
            department_name: New department name
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.c.execute(
                "UPDATE Ogretmenler SET bolum_adi = ? WHERE ogretmen_num = ?",
                (department_name, teacher_id)
            )
            return self.c.rowcount > 0
        except Exception:
            return False
