import sqlite3
import os

db_path = os.path.join(os.getcwd(), "database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(Dersler)")
for row in cursor.fetchall():
    print(row)
conn.close()
