import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database", "okul_veritabani.db")
print("DB Path:", db_path)
if not os.path.exists(db_path):
    print("DB does not exist.")
    exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT DISTINCT sinif_duzeyi FROM Ogrenci_Donemleri")
print("Ogrenci_Donemleri sinif_duzeyi:", c.fetchall())

c.execute("SELECT COUNT(*) FROM Ders_Havuz_Iliskisi")
print("Total Ders_Havuz_Iliskisi:", c.fetchone()[0])

c.execute("SELECT COUNT(*) FROM Ders_Havuz_Iliskisi WHERE sinif_duzeyi = 0")
print("Total Ders_Havuz_Iliskisi with sinif_duzeyi=0:", c.fetchone()[0])

c.execute("SELECT DISTINCT ders_adi, ders_instance, sinif_duzeyi FROM Ders_Havuz_Iliskisi LIMIT 10")
print("Sample Ders_Havuz_Iliskisi:", c.fetchall())

c.execute("SELECT DISTINCT ders_adi, ders_instance FROM Ders_Programi")
prog = c.fetchall()
print("Total Scheduled Courses in Ders_Programi:", len(prog))

pool_names = set()
c.execute("SELECT ders_adi FROM Ders_Havuz_Iliskisi")
for r in c.fetchall():
    pool_names.add(r[0])

scheduled_pools = [p for p in prog if p[0] in pool_names]
print("Total Scheduled POOL Courses in Ders_Programi:", len(scheduled_pools))

if len(scheduled_pools) > 0:
    print("Sample Scheduled Pool Courses:", scheduled_pools[:5])

conn.close()
