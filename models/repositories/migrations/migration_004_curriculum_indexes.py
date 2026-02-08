# -*- coding: utf-8 -*-
"""
Migration 004: Add indexes for Curriculum View performance
"""
import sqlite3

def up(conn: sqlite3.Connection) -> None:
    """
    Add indexes to improve query performance for Curriculum View.
    Targeting:
    - Dersler(ders_kodu, ders_adi) for searching
    - Ders_Havuz_Iliskisi(bolum_num) for filtering by dept
    - Ders_Havuz_Iliskisi(havuz_kodu) for grouping
    """
    indexes = [
        # Search performance (already have ders_adi, adding ders_kodu)
        "CREATE INDEX IF NOT EXISTS idx_dersler_kodu ON Dersler(ders_kodu)",
        
        # Filtering pools by department
        "CREATE INDEX IF NOT EXISTS idx_dhi_bolum ON Ders_Havuz_Iliskisi(bolum_num)",
        
        # Grouping/Filtering by pool code
        "CREATE INDEX IF NOT EXISTS idx_dhi_havuz ON Ders_Havuz_Iliskisi(havuz_kodu)"
    ]
    
    with conn:
        for idx_sql in indexes:
            try:
                conn.execute(idx_sql)
            except sqlite3.OperationalError as e:
                print(f"[MIGRATION] Warning creating index: {e}")
