
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'okul_veritabani.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Dumping Tables ---")

print("\n--- Fakulteler ---")
c.execute("SELECT * FROM Fakulteler")
for row in c.fetchall():
    print(row)

print("\n--- Bolumler ---")
c.execute("SELECT * FROM Bolumler")
for row in c.fetchall():
    print(row)

conn.close()
