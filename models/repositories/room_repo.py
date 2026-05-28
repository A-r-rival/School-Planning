# -*- coding: utf-8 -*-
"""
RoomRepository - Isolates classroom-related data operations
"""
import sqlite3
from datetime import datetime
from typing import List, Tuple, Dict, Optional

class RoomRepository:
    """
    Repository for physical classroom data access.
    """
    def __init__(self, cursor: sqlite3.Cursor, conn: sqlite3.Connection):
        self.c = cursor
        self.conn = conn

    def get_all_classrooms_with_ids(self) -> List[Tuple[int, str, int]]:
        """
        Get all classrooms formatted for the scheduler.
        Returns: List of (derslik_num, derslik_adi, floor)
        """
        try:
            self.c.execute("SELECT derslik_num, derslik_adi, floor FROM Derslikler WHERE silindi = 0")
        except sqlite3.OperationalError:
            self.c.execute("SELECT derslik_num, derslik_adi, 0 as floor FROM Derslikler WHERE silindi = 0")
            
        rows = self.c.fetchall()
        
        # Natural sort helper - sorts "Derslik 2" before "Derslik 10"
        import re
        def natural_sort_key(row):
            text = row[1]
            parts = re.split(r'(\d+)', text)
            converted_parts = []
            for part in parts:
                if part.isdigit():
                    converted_parts.append(int(part))
                else:
                    converted_parts.append(part.lower())
            return converted_parts
            
        return sorted(rows, key=natural_sort_key)

    def derslik_ekle(self, derslik_adi: str, tip: str, kapasite: int, floor: int = 0, ozellikler: str = None, notlar: str = None):
        """Derslik ekle"""
        self.c.execute('''
            INSERT INTO Derslikler (derslik_adi, derslik_tipi, kapasite, floor, ozellikler, notlar)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (derslik_adi, tip, kapasite, floor, ozellikler, notlar))
        
    def derslik_guncelle(self, derslik_num: int, data: dict):
        """Derslik bilgilerini güncelle"""
        query = 'UPDATE Derslikler SET '
        params = []
        updates = []
        for key, value in data.items():
            updates.append(f"{key} = ?")
            params.append(value)
            
        query += ", ".join(updates)
        query += " WHERE derslik_num = ?"
        params.append(derslik_num)
        
        self.c.execute(query, tuple(params))

    def get_derslik_by_id(self, derslik_num: int):
        """Derslik detaylarını getir"""
        try:
            self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, floor, notlar FROM Derslikler WHERE derslik_num = ?', (derslik_num,))
            return self.c.fetchone()
        except sqlite3.OperationalError:
            self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, 0 as floor, "" as notlar FROM Derslikler WHERE derslik_num = ?', (derslik_num,))
            return self.c.fetchone()

    def derslik_sil(self, derslik_num: int):
        """Derslik soft delete - gerçekten silmez, sadece işaretler"""
        self.c.execute('''
            UPDATE Derslikler
            SET silindi = 1, silinme_tarihi = ?
            WHERE derslik_num = ?
        ''', (datetime.now(), derslik_num))

    def aktif_derslikleri_getir(self):
        """Sadece aktif (silinmemiş) derslikleri getir"""
        try:
            self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, floor, notlar FROM Derslikler WHERE silindi = 0')
            return self.c.fetchall()
        except sqlite3.OperationalError:
            self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, 0 as floor, "" as notlar FROM Derslikler WHERE silindi = 0')
            return self.c.fetchall()

    def tum_derslikleri_getir(self):
        """Tüm derslikleri getir (silinmiş olanlar dahil)"""
        try:
            self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, silindi, silinme_tarihi, floor, notlar FROM Derslikler')
            return self.c.fetchall()
        except sqlite3.OperationalError:
            self.c.execute('SELECT derslik_num, derslik_adi, derslik_tipi, kapasite, silindi, silinme_tarihi, 0 as floor, "" as notlar FROM Derslikler')
            return self.c.fetchall()
