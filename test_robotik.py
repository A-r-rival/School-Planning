import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'school_data.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

c.execute("SELECT * FROM Dersler WHERE ders_adi LIKE '%Robotik%'")
print("Dersler:", c.fetchall())

c.execute("SELECT * FROM Ders_Sinif_Iliskisi dsi JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num JOIN Bolumler b ON od.bolum_num = b.bolum_id WHERE dsi.ders_adi LIKE '%Robotik%'")
print("\nDers_Sinif_Iliskisi (Core):")
for row in c.fetchall():
    print(row)
    
c.execute("SELECT * FROM Ders_Havuz_Iliskisi dhi JOIN Bolumler b ON dhi.bolum_id = b.bolum_id WHERE dhi.ders_adi LIKE '%Robotik%'")
print("\nDers_Havuz_Iliskisi (Pool):")
for row in c.fetchall():
    print(row)
