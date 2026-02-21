import sqlite3
import os

db_path = os.path.join("database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Ders_Programi Sample ---")
c.execute("SELECT program_id, ders_adi, derslik_id FROM Ders_Programi LIMIT 20")
for row in c.fetchall():
    print(row)

print("\n--- Courses with 'Lab' in name anywhere ---")
c.execute("SELECT ders_adi FROM Dersler WHERE ders_adi LIKE '%Lab%' LIMIT 10")
for row in c.fetchall():
    print(row)

conn.close()
