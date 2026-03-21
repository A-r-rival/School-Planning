import sqlite3
import os

db_path = os.path.join("d:\\Git_Projects\\School-Planning", "database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("PRAGMA table_info(Ogretmen_Musaitlik)")
    cols = c.fetchall()
    print("Columns in Ogretmen_Musaitlik:")
    for col in cols:
        print(f" - {col[1]} ({col[2]})")

    # Check migrations
    c.execute("SELECT migration_name FROM schema_migrations")
    migs = c.fetchall()
    print("\nApplied Migrations:")
    for m in migs:
        print(f" - {m[0]}")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
