import sqlite3
import os

db_path = os.path.join("database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Room Types in Derslikler Table ---")
c.execute("SELECT derslik_num, derslik_adi, derslik_tipi FROM Derslikler LIMIT 20")
for row in c.fetchall():
    print(row)

print("\n--- Room Types in Ders_Programi (Join Test) ---")
c.execute("""
    SELECT DISTINCT dp.derslik_id, dlk.derslik_tipi 
    FROM Ders_Programi dp
    LEFT JOIN Derslikler dlk ON dp.derslik_id = dlk.derslik_num
    LIMIT 20
""")
for row in c.fetchall():
    print(row)

conn.close()
