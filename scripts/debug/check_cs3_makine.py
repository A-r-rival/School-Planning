# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

print("What CS 3rd year students see for Makine courses:")
print("=" * 80)

c.execute("""
    SELECT 
        dp.gun as Day,
        dp.baslangic as Start,
        dp.bitis as End,
        dp.ders_adi as CourseName,
        d.ders_kodu as CourseCode,
        dp.ders_instance as Instance,
        dp.ders_tipi as Type
    FROM Ders_Programi dp
    JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    JOIN Bolumler b ON od.bolum_num = b.bolum_id
    WHERE b.bolum_adi LIKE '%Bilgisayar%' 
      AND od.sinif_duzeyi = 3
      AND dp.ders_adi LIKE '%Makine%'
    ORDER BY dp.gun, dp.baslangic, dp.ders_instance
""")

count = 0
for row in c.fetchall():
    count += 1
    print(f"{count}. {row}")

print(f"\nTotal entries: {count}")

conn.close()
