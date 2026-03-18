import sqlite3

def up(conn: sqlite3.Connection):
    """
    Creates the Ortak_Ders_Gruplari table.
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Ortak_Ders_Gruplari (
            grup_id INTEGER NOT NULL,
            ders_adi TEXT NOT NULL,
            ders_instance INTEGER NOT NULL,
            PRIMARY KEY (grup_id, ders_adi, ders_instance)
        )
    """)
    
    conn.commit()
