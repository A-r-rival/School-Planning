import sqlite3
import os

def migrate_db():
    db_path = 'okul_veritabani.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    try:
        # Check if column already exists
        c.execute("PRAGMA table_info(Ders_Programi)")
        columns = [info[1] for info in c.fetchall()]
        
        if 'ders_tipi' not in columns:
            print("Adding 'ders_tipi' column to Ders_Programi...")
            c.execute("ALTER TABLE Ders_Programi ADD COLUMN ders_tipi TEXT DEFAULT 'Ders'")
            conn.commit()
            print("Migration successful.")
        else:
            print("'ders_tipi' column already exists.")

    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_db()
