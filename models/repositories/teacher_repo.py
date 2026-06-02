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

    def get_all_teachers_with_ids(self) -> List[Tuple[int, str, Optional[str]]]:
        """Get all teachers with their IDs and room preferences"""
        try:
            # Check if column exists first to be safe (migration should have added it)
            self.c.execute("SELECT ogretmen_num, ad || ' ' || soyad, room_request FROM Ogretmenler ORDER BY ad")
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching teachers: {e}")
            return []
            

    def get_teacher_unavailability(self, teacher_id: int, yil: str = None, donem: str = None) -> List[tuple]:
        """Get all unavailable slots for a teacher"""
        try:
            # Controller expects: (day, start, end, id, description, ...)
            query = '''
                SELECT om.gun, om.baslangic, om.bitis, om.id, om.description, o.preferred_day_span, om.yil, om.donem
                FROM Ogretmen_Musaitlik om
                JOIN Ogretmenler o ON om.ogretmen_id = o.ogretmen_num
                WHERE om.ogretmen_id = ? 
            '''
            params = [teacher_id]
            
            if yil:
                query += " AND (om.yil = 'Hepsi' OR om.yil = ?)"
                params.append(yil)
                
            if donem:
                query += " AND (om.donem = 'Hepsi' OR om.donem = ?)"
                params.append(donem)
                
            query += '''
                ORDER BY 
                    CASE om.gun 
                        WHEN 'Pazartesi' THEN 1 
                        WHEN 'Salı' THEN 2 
                        WHEN 'Çarşamba' THEN 3 
                        WHEN 'Perşembe' THEN 4 
                        WHEN 'Cuma' THEN 5 
                        WHEN 'Cumartesi' THEN 6 
                        WHEN 'Pazar' THEN 7 
                    END, om.baslangic
            '''
            self.c.execute(query, tuple(params))
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching unavailability: {e}")
            return []
    def get_combined_availability(self, teacher_id: int = None) -> List[dict]:
        """
        Get both Day Spans and Unavailability Slots combined.
        Returns list of dicts:
        {
            'type': 'span' | 'slot',
            'teacher_id': int,
            'teacher_name': str,
            # For Span:
            'span_value': int,
            # For Slot:
            'id': int,
            'day': str,
            'start': str,
            'end': str,
            'yil': str,
            'donem': str,
            'description': str
        }
        """
        results = []
        try:
            # 1. Fetch Teachers (Filtered or All)
            if teacher_id:
                self.c.execute("SELECT ogretmen_num, ad, soyad, preferred_day_span, room_request FROM Ogretmenler WHERE ogretmen_num = ?", (teacher_id,))
            else:
                self.c.execute("SELECT ogretmen_num, ad, soyad, preferred_day_span, room_request FROM Ogretmenler ORDER BY ad, soyad")
            
            teachers = self.c.fetchall()
            
            for t in teachers:
                t_num, t_ad, t_soyad, t_span, t_room = t
                t_name = f"{t_ad} {t_soyad}"
                
                # Add Span Entry if exists or if we need to pass room_pref to UI
                if (t_span and t_span > 0) or t_room:
                    results.append({
                        'type': 'span',
                        'teacher_id': t_num,
                        'teacher_name': t_name,
                        'span_value': t_span or 0,
                        'room_pref': t_room or ""
                    })
                
                # 2. Fetch Slots for this teacher
                self.c.execute('''
                    SELECT id, gun, baslangic, bitis, yil, donem, description 
                    FROM Ogretmen_Musaitlik 
                    WHERE ogretmen_id = ?
                    ORDER BY 
                    CASE gun 
                        WHEN 'Pazartesi' THEN 1 
                        WHEN 'Salı' THEN 2 
                        WHEN 'Çarşamba' THEN 3 
                        WHEN 'Perşembe' THEN 4 
                        WHEN 'Cuma' THEN 5 
                        WHEN 'Cumartesi' THEN 6 
                        WHEN 'Pazar' THEN 7 
                    END, baslangic
                ''', (t_num,))
                slots = self.c.fetchall()
                
                for s in slots:
                    results.append({
                        'type': 'slot',
                        'teacher_id': t_num,
                        'teacher_name': t_name,
                        'id': s[0],
                        'day': s[1],
                        'start': s[2],
                        'end': s[3],
                        'yil': s[4],
                        'donem': s[5],
                        'description': s[6]
                    })
                    
            return results
            
        except Exception as e:
            print(f"Error fetching combined availability: {e}")
            return []
    def remove_teacher_unavailability(self, unavailability_id: int) -> bool:
        """Remove an unavailability slot"""
        try:
            self.c.execute("DELETE FROM Ogretmen_Musaitlik WHERE id = ?", (unavailability_id,))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error removing teacher unavailability: {e}")
            raise
    def get_teacher_span(self, teacher_id: int) -> int:
        """Get preferred day span for a teacher"""
        try:
            self.c.execute("SELECT preferred_day_span FROM Ogretmenler WHERE ogretmen_num = ?", (teacher_id,))
            row = self.c.fetchone()
            # Return 0 if NULL or not set
            return row[0] if row and row[0] is not None else 0
        except Exception as e:
            print(f"Error getting teacher span: {e}")
            return 0
    def get_all_teacher_day_spans(self) -> List[tuple]:
        """Get (teacher_id, preferred_day_span) for all teachers with a span set."""
        try:
            self.c.execute(
                "SELECT ogretmen_num, preferred_day_span FROM Ogretmenler "
                "WHERE preferred_day_span IS NOT NULL AND preferred_day_span > 0"
            )
            return self.c.fetchall()
        except Exception as e:
            print(f"Error fetching teacher day spans: {e}")
            return []
    def update_teacher_span(self, teacher_id: int, span: int) -> bool:
        """Update preferred day span for a teacher"""
        try:
            # Clean span value: 0 for "No Constraint"
            val = span if span > 0 else None
            self.c.execute("UPDATE Ogretmenler SET preferred_day_span = ? WHERE ogretmen_num = ?", (val, teacher_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating teacher span: {e}")
            raise
    def get_teacher_room_request(self, teacher_id: int) -> str:
        """Get room request note for a teacher"""
        try:
            self.c.execute("SELECT room_request FROM Ogretmenler WHERE ogretmen_num = ?", (teacher_id,))
            row = self.c.fetchone()
            return row[0] if row and row[0] else ""
        except Exception as e:
            print(f"Error getting room request: {e}")
            return ""
    def update_teacher_room_request(self, teacher_id: int, request: str) -> bool:
        """Update room request note for a teacher"""
        try:
            val = request if request.strip() else None
            self.c.execute("UPDATE Ogretmenler SET room_request = ? WHERE ogretmen_num = ?", (val, teacher_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating room request: {e}")
            raise

    # ════════════════════════════════════════════════════════════════
    # MASTER VIEW & SNAPSHOTS
    # ════════════════════════════════════════════════════════════════

    def add_teacher_unavailability(self, teacher_id: int, day: str, start_time: str, end_time: str, yil: str = "Hepsi", donem: str = "Hepsi", description: str = "") -> bool:
        """
        Add a time slot where the teacher is NOT available.
        """
        try:
            # Check for existing overlap for this teacher within the same year/semester scope
            self.c.execute('''
                SELECT id FROM Ogretmen_Musaitlik 
                WHERE ogretmen_id = ? AND gun = ? AND yil = ? AND donem = ?
                AND (
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic >= ? AND bitis <= ?)
                )
            ''', (teacher_id, day, yil, donem, start_time, start_time, end_time, end_time, start_time, end_time))
            
            if self.c.fetchone():
                return False # Already marked as unavailable
            
            self.c.execute('''
                INSERT INTO Ogretmen_Musaitlik (ogretmen_id, gun, baslangic, bitis, yil, donem, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (teacher_id, day, start_time, end_time, yil, donem, description))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error adding teacher unavailability: {e}")
            raise
    def update_teacher_unavailability(self, u_id: int, teacher_id: int, day: str, start: str, end: str, yil: str = "Hepsi", donem: str = "Hepsi", description: str = "") -> bool:
        """Update unavailability slot"""
        try:
            # Check for existing overlap (excluding self)
            self.c.execute('''
                SELECT id FROM Ogretmen_Musaitlik 
                WHERE ogretmen_id = ? AND gun = ? AND yil = ? AND donem = ? AND id != ?
                AND (
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic <= ? AND bitis >= ?) OR
                    (baslangic >= ? AND bitis <= ?)
                )
            ''', (teacher_id, day, yil, donem, u_id, start, start, end, end, start, end))
            
            if self.c.fetchone():
                return False # Overlap
            
            self.c.execute('''
                UPDATE Ogretmen_Musaitlik 
                SET gun = ?, baslangic = ?, bitis = ?, yil = ?, donem = ?, description = ?
                WHERE id = ?
            ''', (day, start, end, yil, donem, description, u_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error updating teacher unavailability: {e}")
            raise



    # ════════════════════════════════════════════════════════════════
    # STUDENT QUERIES & GRADES
    # ════════════════════════════════════════════════════════════════
