import sqlite3

def up(conn: sqlite3.Connection):
    """
    Adds 'ogrenci_sayisi' column to 'Ogrenci_Donemleri' table.
    Default size is 0 to avoid breaking existing logic.
    """
    cursor = conn.cursor()
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(Ogrenci_Donemleri)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'ogrenci_sayisi' not in columns:
        cursor.execute("ALTER TABLE Ogrenci_Donemleri ADD COLUMN ogrenci_sayisi INTEGER DEFAULT 0")
        print("[MIGRATION] Added 'ogrenci_sayisi' column to 'Ogrenci_Donemleri'.")
    else:
        print("[MIGRATION] Column 'ogrenci_sayisi' already exists in 'Ogrenci_Donemleri'.")

def down(cursor: sqlite3.Cursor):
    """
    Since SQLite ALTER TABLE DROP COLUMN is only supported in newer versions, 
    we just pass or leave it as is for safety.
    """
    pass
