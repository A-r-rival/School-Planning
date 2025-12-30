# Simple verification - just check the core facts
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# How many Makine course entries?
c.execute("SELECT COUNT(*) FROM Dersler WHERE ders_adi LIKE '%Makine%'")
total = c.fetchone()[0]

# How many unique names?
c.execute("SELECT COUNT(DISTINCT ders_adi) FROM Dersler WHERE ders_adi LIKE '%Makine%'")
unique = c.fetchone()[0]

# CS 3rd year sees how many?
c.execute("""
    SELECT COUNT(DISTINCT d.ders_kodu)
    FROM Ders_Programi dp
    JOIN Dersler d ON d.ders_adi = dp.ders_adi AND d.ders_instance = dp.ders_instance
    JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    JOIN Bolumler b ON od.bolum_num = b.bolum_id
    WHERE b.bolum_adi LIKE '%Bilgisayar%'
      AND od.sinif_duzeyi = 3
      AND d.ders_adi LIKE '%Makine%'
""")
cs3_count = c.fetchone()[0]

conn.close()

print(f"Total Makine entries in Dersler: {total}")
print(f"Unique Makine course names: {unique}")
print(f"CS 3rd year sees: {cs3_count} course(s)")
print()
if total == unique and cs3_count == 1:
    print("SUCCESS - Migration worked!")
else:
    print("NEEDS REVIEW - Check details")
