import sqlite3
import os

db_path = os.path.join("database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Derslikler ID Range ---")
c.execute("SELECT MIN(derslik_num), MAX(derslik_num), COUNT(*) FROM Derslikler")
print(c.fetchone())

print("\n--- Ders_Programi Derslik ID Range ---")
c.execute("SELECT MIN(derslik_id), MAX(derslik_id), COUNT(DISTINCT derslik_id) FROM Ders_Programi")
print(c.fetchone())

print("\n--- Example Matches (if any) ---")
c.execute("""
    SELECT dlk.derslik_num, dlk.derslik_adi 
    FROM Derslikler dlk 
    WHERE dlk.derslik_num IN (SELECT DISTINCT derslik_id FROM Ders_Programi)
    LIMIT 10
""")
print(c.fetchall())

conn.close()
