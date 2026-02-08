# -*- coding: utf-8 -*-
"""
Migration 006: Add derslik_id and ders_tipi to Ders_Programi table.
Required for saving schedule results with room assignments and course types.
"""
import sqlite3

def up(conn: sqlite3.Connection) -> None:
    """
    Add 'derslik_id' and 'ders_tipi' columns to Ders_Programi.
    """
    c = conn.cursor()
    
    # Check if columns exist to avoid errors
    c.execute("PRAGMA table_info(Ders_Programi)")
    columns = [info[1] for info in c.fetchall()]
    
    if "derslik_id" not in columns:
        print("[MIGRATION] Adding 'derslik_id' column to Ders_Programi...")
        # derslik_id can be null if no room assigned? Or mandatory? Scheduler assigns it.
        # It's an integer referencing Derslikler(derslik_num) usually, but scheduler might pass name?
        # Let's assume INTEGER for now as it's an ID.
        c.execute("ALTER TABLE Ders_Programi ADD COLUMN derslik_id INTEGER REFERENCES Derslikler(derslik_num)")
        print("[MIGRATION] ✅ Column 'derslik_id' added.")
        
    if "ders_tipi" not in columns:
        print("[MIGRATION] Adding 'ders_tipi' column to Ders_Programi...")
        c.execute("ALTER TABLE Ders_Programi ADD COLUMN ders_tipi TEXT")
        print("[MIGRATION] ✅ Column 'ders_tipi' added.")
        
    conn.commit()
