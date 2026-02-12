import sqlite3

def up(conn: sqlite3.Connection) -> None:
    """
    Migration: Add room_request to Ogretmenler and floor to Derslikler
    """
    cursor = conn.cursor()
    
    # 1. Add room_request to Ogretmenler - Using PRAGMA table_info is safer for column check but operational error works
    # Check explicitly using PRAGMA to be safe
    cursor.execute("PRAGMA table_info(Ogretmenler)")
    cols = {row[1] for row in cursor.fetchall()}
    if "room_request" not in cols:
        print("[MIGRATION] Adding room_request column to Ogretmenler")
        conn.execute("ALTER TABLE Ogretmenler ADD COLUMN room_request TEXT")

    # 2. Add floor to Derslikler
    cursor.execute("PRAGMA table_info(Derslikler)")
    cols = {row[1] for row in cursor.fetchall()}
    if "floor" not in cols:
        print("[MIGRATION] Adding floor column to Derslikler")
        conn.execute("ALTER TABLE Derslikler ADD COLUMN floor INTEGER DEFAULT 0")
