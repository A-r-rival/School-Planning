import sqlite3
import sys

db_path = "d:/Git_Projects/School-Planning/database/school_data.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

bolum_id = 1  # Assuming Bilgisayar Müh is 1. We'll search by name just to be sure.
c.execute("SELECT bolum_id FROM Bolumler WHERE bolum_adi LIKE '%Bilgisayar%'")
row = c.fetchone()
if row:
    bolum_id = row[0]
else:
    print("Bilgisayar Müh not found")
    sys.exit()

sinif = 3

query = '''
SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu, dp.ders_tipi
FROM Ders_Programi dp
LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
JOIN Ders_Sinif_Iliskisi dsi ON dsi.ders_instance = d.ders_instance AND dsi.ders_adi = d.ders_adi
JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
WHERE od.bolum_num = ? AND od.sinif_duzeyi = ?

UNION ALL

SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
       (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
       (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
       COALESCE(d.ders_kodu, 'CUSTOM') as ders_kodu, dp.ders_tipi
FROM Ders_Programi dp
LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
JOIN Ders_Havuz_Iliskisi dhi ON dhi.ders_instance = d.ders_instance AND dhi.ders_adi = d.ders_adi
JOIN Ogrenci_Donemleri od ON od.bolum_num = dhi.bolum_id AND od.sinif_duzeyi = dhi.sinif_duzeyi
WHERE od.bolum_num = ? AND od.sinif_duzeyi = ?
'''

c.execute(query, (bolum_id, sinif, bolum_id, sinif))
results = c.fetchall()

print(f"Total rows fetched for Dept {bolum_id}, Year {sinif}: {len(results)}")
for r in results:
    is_elect = "SD" in str(r[6]).upper() or "Seçmeli" in str(r[3])
    flag = "ELECTIVE/POOL" if is_elect else "CORE"
    print(f"[{flag}] {r[6]} - {r[3]} ({r[7]}) on {r[0]} {r[1]}-{r[2]}")

print("\n--- Checking raw Ders_Programi for any SD classes ---")
c.execute("SELECT ders_adi, ders_instance FROM Ders_Programi WHERE ders_adi LIKE '%Seçmeli%' OR ders_adi LIKE '%SD%'")
sd_courses = c.fetchall()
print(f"SD courses in Ders_Programi: {len(sd_courses)}")
for sc in sd_courses:
    print(sc)
