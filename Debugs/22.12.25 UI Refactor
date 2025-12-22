
import sqlite3
import os

def migrate_schema():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "okul_veritabani.db")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    print("Dropping old Derslikler table...")
    try:
        c.execute("DROP TABLE IF EXISTS Derslikler")
    except Exception as e:
        print(f"Error dropping table: {e}")

    print("Recreating Derslikler table...")
    # New definition matching schedule_model.py
    c.execute('''CREATE TABLE IF NOT EXISTS Derslikler (
                derslik_num INTEGER PRIMARY KEY AUTOINCREMENT,
                derslik_adi TEXT NOT NULL,
                derslik_tipi TEXT,
                kapasite INTEGER NOT NULL,
                ozellikler TEXT,
                silindi BOOLEAN DEFAULT 0,
                silinme_tarihi DATETIME
            )''')
    
    conn.commit()
    conn.close()
    print("Migration complete.")

if __name__ == "__main__":
    migrate_schema()
