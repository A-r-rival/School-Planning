import sys
import sqlite3
import os

# Add project root to sys.path
sys.path.insert(0, r"d:\Git_Projects\School-Planning")

from models.repositories.migration import DatabaseMigration

db_path = os.path.join(r"d:\Git_Projects\School-Planning", "database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)

try:
    print("Testing Migration Script manually...")
    migrator = DatabaseMigration(conn)
    migrator.run_all()
    print("All migrations completed without exceptions.")
    
    cursor = conn.execute("PRAGMA table_info(Ogretmen_Musaitlik)")
    cols = [row[1] for row in cursor.fetchall()]
    print("Current columns in Ogretmen_Musaitlik:")
    for c in cols:
        print(f" - {c}")
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    conn.close()
