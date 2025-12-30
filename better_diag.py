# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
cursor = conn.cursor()

# Issue 1: Check pool relationships
print("ISSUE 1: Pool Information")
print("=" * 80)

cursor.execute("""
    SELECT dhi.*, d.ders_kodu
    FROM Ders_Havuz_Iliskisi dhi
    LEFT JOIN Dersler d ON dhi.ders_adi = d.ders_adi AND dhi.ders_instance = d.ders_instance
    WHERE dhi.ders_adi LIKE '%Makine%'
    LIMIT 5
""")
print("Pool relationships for Makine courses:")
for row in cursor.fetchall():
    print(row)

# Issue 2: Check schedule entries
print("\n" + "=" * 80)
print("ISSUE 2: Schedule Entries and Time Slots")
print("=" * 80)

cursor.execute("""
    SELECT dp.ders_adi, dp.ders_instance, dp.gun, dp.baslangic, dp.bitis, d.ders_kodu,
           GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi)
    FROM Ders_Programi dp
    LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
    WHERE dp.ders_adi LIKE '%Makine%'
    GROUP BY dp.program_id
    ORDER BY dp.gun, dp.baslangic
""")
print("Schedule entries for Makine courses:")
for row in cursor.fetchall():
    print(row)

conn.close()
