# -*- coding: utf-8 -*-
"""
Migration 012: Add sinif_duzeyi to Ders_Havuz_Iliskisi
Adds class year level to pool course relationships so the scheduler
can correctly filter which student groups are affected by each pool course.
"""
import sqlite3


def up(conn: sqlite3.Connection) -> None:
    c = conn.cursor()
    # Check if column already exists
    c.execute("PRAGMA table_info(Ders_Havuz_Iliskisi)")
    columns = [col[1] for col in c.fetchall()]
    if 'sinif_duzeyi' not in columns:
        conn.execute("ALTER TABLE Ders_Havuz_Iliskisi ADD COLUMN sinif_duzeyi INTEGER DEFAULT 0")
        print("[MIGRATION] Added 'sinif_duzeyi' column to 'Ders_Havuz_Iliskisi'.")
    else:
        print("[MIGRATION] Column 'sinif_duzeyi' already exists in 'Ders_Havuz_Iliskisi'.")
