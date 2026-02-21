import sqlite3
import os

db_path = os.path.join("database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Derslikler Schema ---")
c.execute("PRAGMA table_info(Derslikler)")
for col in c.fetchall():
    print(col)

print("\n--- Derslikler Sample Data (All Columns) ---")
c.execute("SELECT * FROM Derslikler LIMIT 20")
cols = [d[0] for d in c.description]
print(cols)
for row in c.fetchall():
    print(row)

print("\n--- Rows in Ders_Programi with their Classroom Info ---")
c.execute("""
    SELECT dp.program_id, dp.derslik_id, dlk.derslik_adi, dlk.derslik_tipi
    FROM Ders_Programi dp
    LEFT JOIN Derslikler dlk ON dp.derslik_id = dlk.derslik_num
    LIMIT 10
""")
for row in c.fetchall():
    print(row)

conn.close()
