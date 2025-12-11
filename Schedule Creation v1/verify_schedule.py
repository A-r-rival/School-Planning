
import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'okul_veritabani.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Schedule Verification ---")
c.execute("SELECT COUNT(*) FROM Ders_Programi")
total_slots = c.fetchone()[0]
print(f"Total Scheduled Slots: {total_slots}")

print("\n--- By Dept ---")
# This is tricky because Ders_Programi doesn't have department.
# We join via Dersler -> Ders_Sinif_Iliskisi -> Ogrenci_Donemleri -> Bolumler
c.execute("""
    SELECT b.bolum_adi, COUNT(*) 
    FROM Ders_Programi dp
    JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    JOIN Bolumler b ON od.bolum_num = b.bolum_id
    GROUP BY b.bolum_adi
""")
for row in c.fetchall():
    print(f"{row[0]}: {row[1]}")

print("\n--- Sample Schedule ---")
c.execute("SELECT * FROM Ders_Programi LIMIT 10")
for row in c.fetchall():
    print(row)

conn.close()
