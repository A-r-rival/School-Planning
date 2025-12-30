# Check which exact Makine courses exist
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

print("All Makine courses in Dersler:")
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_adi, ders_instance
""")

courses = {}
for row in c.fetchall():
    name = row[1]
    if name not in courses:
        courses[name] = []
    courses[name].append((row[0], row[2]))

for name, instances in courses.items():
    print(f"\n{name}:")
    for code, inst in instances:
        print(f"  [{code}] instance={inst}")
    if len(instances) > 1:
        print(f"  ⚠️ DUPLICATE - {len(instances)} instances")

print("\n" + "=" * 80)
print("What CS 3rd year sees:")
c.execute("""
    SELECT d.ders_kodu, d.ders_adi, d.ders_instance
    FROM Ders_Programi dp
    JOIN Dersler d ON d.ders_adi = dp.ders_adi AND d.ders_instance = dp.ders_instance
    JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    JOIN Bolumler b ON od.bolum_num = b.bolum_id
    WHERE b.bolum_adi LIKE '%Bilgisayar%'
      AND od.sinif_duzeyi = 3
      AND d.ders_adi LIKE '%Makine%'
    ORDER BY d.ders_adi
""")

for row in c.fetchall():
    print(f"  [{row[0]}] {row[1]} (instance={row[2]})")

conn.close()
