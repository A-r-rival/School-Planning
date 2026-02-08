# -*- coding: utf-8 -*-
"""
Migration 005: Add 'description' column to Ogretmen_Musaitlik table.
"""
import sqlite3

def add_description_to_unavailability(conn: sqlite3.Connection) -> None:
    """
    Adds 'description' column to Ogretmen_Musaitlik table.
    """
    try:
        # Check if column exists
        cursor = conn.execute("PRAGMA table_info(Ogretmen_Musaitlik)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if "description" not in columns:
            print("[MIGRATION] Adding 'description' column to Ogretmen_Musaitlik...")
            conn.execute("ALTER TABLE Ogretmen_Musaitlik ADD COLUMN description TEXT DEFAULT ''")
            print("[MIGRATION] ✅ Column 'description' added.")
        else:
            print("[MIGRATION] Column 'description' already exists in Ogretmen_Musaitlik.")
            
    except Exception as e:
        print(f"[MIGRATION] ❌ Error adding description column: {e}")
