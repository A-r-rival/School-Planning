# -*- coding: utf-8 -*-
"""
StudentRepository - Isolates student-related data operations
"""
import sqlite3
from typing import List, Tuple, Dict, Optional

class StudentRepository:
    """
    Repository for student data access.
    """
    def __init__(self, cursor: sqlite3.Cursor, conn: sqlite3.Connection):
        self.c = cursor
        self.conn = conn

    def get_students(self, filters: Dict[str, any] = None) -> List[tuple]:
        """
        Get students with optional filters.
        Returns: List of (ogrenci_num, ad, soyad, bolum_adi, sinif)
        """
        try:
            query = """
                SELECT o.ogrenci_num, o.ad, o.soyad, b.bolum_adi, o.kacinci_donem
                FROM Ogrenciler o
                JOIN Bolumler b ON o.bolum_num = b.bolum_id
                WHERE 1=1
            """
            params = []
            
            if filters:
                if filters.get('bolum_id'):
                    query += " AND o.bolum_num = ?"
                    params.append(filters['bolum_id'])
                
                if filters.get('sinif'):
                    effective_donem = int(filters['sinif']) * 2
                    query += f" AND o.kacinci_donem IN ({effective_donem}, {effective_donem - 1})"
                    
                if filters.get('search'):
                    search_term = f"%{filters['search']}%"
                    query += " AND (o.ad LIKE ? OR o.soyad LIKE ? OR CAST(o.ogrenci_num AS TEXT) LIKE ?)"
                    params.extend([search_term, search_term, search_term])
                    
                if filters.get('types'):
                    types = filters['types']
                    type_conditions = []
                    
                    for t in types:
                        if t == 'Anadal':
                            # Actually, kacinci_donem could be anything. So just NO ikinci_bolum_turu or it is anadal
                            type_conditions.append("(o.ikinci_bolum_turu IS NULL OR o.ikinci_bolum_turu = 'anadal')")
                        elif t == 'Yandal/ÇAP':
                            type_conditions.append("(o.ikinci_bolum_turu IS NOT NULL AND o.ikinci_bolum_turu != 'anadal')")
                            
                    if type_conditions:
                        query += " AND (" + " OR ".join(type_conditions) + ")"
                        
            query += " ORDER BY o.ad, o.soyad"
            
            self.c.execute(query, tuple(params))
            return self.c.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Error getting students: {e}")
            return []

    def get_student_grades(self, student_id: int, show_history: bool = False) -> List[tuple]:
        """
        Get grades for a specific student.
        Returns: List of (ders_kodu, ders_adi, akts, harf_notu, donem)
        """
        try:
            if show_history:
                self.c.execute("""
                    SELECT d.ders_kodu, d.ders_adi, d.akts, t1.harf_notu, t1.donem
                    FROM Ogrenci_Notlari t1
                    JOIN Dersler d ON t1.ders_adi = d.ders_adi
                    WHERE t1.ogrenci_num = ?
                    ORDER BY t1.donem DESC, d.ders_adi
                """, (student_id,))
            else:
                self.c.execute("""
                    SELECT d.ders_kodu, d.ders_adi, d.akts, t1.harf_notu, t1.donem
                    FROM Ogrenci_Notlari t1
                    LEFT JOIN Ogrenci_Notlari t2 ON t1.id = t2.onceki_not_id
                    JOIN Dersler d ON t1.ders_adi = d.ders_adi
                    WHERE t1.ogrenci_num = ? AND t2.id IS NULL
                    ORDER BY t1.donem DESC, d.ders_adi
                """, (student_id,))
            return self.c.fetchall()
        except sqlite3.OperationalError as e:
            print(f"Error getting student grades: {e}")
            return []
