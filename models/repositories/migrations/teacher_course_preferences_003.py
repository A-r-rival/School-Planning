# -*- coding: utf-8 -*-
"""
Migration: Add Teacher Course Preferences Table
"""
import sqlite3

def up(conn: sqlite3.Connection) -> None:
    """
    Creates Ogretmen_Ders_Tercihleri table.
    """
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS Ogretmen_Ders_Tercihleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ogretmen_id INTEGER NOT NULL,
                ders_adi TEXT NOT NULL,
                ders_secim_notu TEXT,
                tercih_tipi TEXT CHECK(tercih_tipi IN ('WANTED', 'BLOCKED')),
                FOREIGN KEY (ogretmen_id) REFERENCES Ogretmenler(ogretmen_num) ON DELETE CASCADE,
                UNIQUE(ogretmen_id, ders_adi)
            )
        """)
        # Create index for faster lookups by teacher
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_tercihler_ogretmen 
            ON Ogretmen_Ders_Tercihleri(ogretmen_id)
        """)
