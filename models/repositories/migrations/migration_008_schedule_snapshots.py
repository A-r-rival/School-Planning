
import sqlite3

def create_schedule_snapshots_table(conn: sqlite3.Connection):
    """
    Creates the schedule_snapshots table for storing past schedules.
    """
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schedule_snapshots'")
    if cursor.fetchone():
        return

    # Create table
    cursor.execute("""
        CREATE TABLE schedule_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            semester TEXT,
            data JSON NOT NULL
        )
    """)
    
    conn.commit()
