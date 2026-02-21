# -*- coding: utf-8 -*-
import sqlite3

def up(conn: sqlite3.Connection) -> None:
    """Add notlar column to Derslikler table."""
    # Check if column already exists
    cursor = conn.execute("PRAGMA table_info(Derslikler)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'notlar' not in columns:
        with conn:
            conn.execute("ALTER TABLE Derslikler ADD COLUMN notlar TEXT")
