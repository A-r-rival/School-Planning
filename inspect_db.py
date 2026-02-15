
import sqlite3
import os

db_path = os.path.join("database", "okul_veritabani.db")
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Ogrenci_Donemleri Schema ---")
try:
    c.execute("SELECT DISTINCT sinif_duzeyi FROM Ogrenci_Donemleri ORDER BY sinif_duzeyi")
    print(f"Distinct sinif_duzeyi values: {c.fetchall()}")
except Exception as e:
    print(e)


    for row in c.fetchall():
        print(row)
except Exception as e:
    print(e)
