import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'school_data.db')
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("--- Ders_Programi for Mekatronik Müh ---")
# Let's get the schedule directly
c.execute("""
    SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi, dp.ders_tipi
    FROM Ders_Programi dp
    WHERE dp.ders_adi LIKE '%Robotik%' OR dp.ders_adi LIKE '%Kontrol M%'
""")
for row in c.fetchall():
    print(row)

print("\--- Ders_Sinif_Iliskisi ve Ders_Havuz_Iliskisi ---")
c.execute("SELECT * FROM Ders_Havuz_Iliskisi WHERE ders_adi LIKE '%Robotik%'")
print("Havuz (Robotik):", c.fetchall())

c.execute("SELECT * FROM Ders_Sinif_Iliskisi WHERE ders_adi LIKE '%Kontrol%'")
print("Sinif (Kontrol):", c.fetchall())
