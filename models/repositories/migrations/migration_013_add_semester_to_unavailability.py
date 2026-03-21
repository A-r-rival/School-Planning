import sqlite3

def up(conn: sqlite3.Connection) -> None:
    """Adds yil and donem columns to Ogretmen_Musaitlik table."""
    cursor = conn.execute("PRAGMA table_info(Ogretmen_Musaitlik)")
    columns = {row[1] for row in cursor.fetchall()}
    
    with conn:
        if 'yil' not in columns:
            conn.execute("ALTER TABLE Ogretmen_Musaitlik ADD COLUMN yil TEXT DEFAULT 'Hepsi'")
            print("[MIGRATION] Added 'yil' column to 'Ogretmen_Musaitlik'.")
        if 'donem' not in columns:
            conn.execute("ALTER TABLE Ogretmen_Musaitlik ADD COLUMN donem TEXT DEFAULT 'Hepsi'")
            print("[MIGRATION] Added 'donem' column to 'Ogretmen_Musaitlik'.")
        
        if 'yil' in columns and 'donem' in columns:
            print("[MIGRATION] Columns 'yil' and 'donem' already exist in 'Ogretmen_Musaitlik'.")
