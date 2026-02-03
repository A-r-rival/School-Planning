# -*- coding: utf-8 -*-
import sqlite3
import sys

# Write to file to avoid terminal corruption
output_file = open('investigation_results.txt', 'w', encoding='utf-8')

def log(msg):
    print(msg)
    output_file.write(msg + '\n')

conn = sqlite3.connect('okul_veritabani.db')
cursor = conn.cursor()

log("=" * 100)
log("INVESTIGATION: Elective Course Display Issues")
log("=" * 100)

# ========== ISSUE 1: Pool Information ==========
log("\n" + "=" * 100)
log("ISSUE 1: Pool Information for Elective Courses")
log("=" * 100)

# Check Ders_Havuz_Iliskisi table structure
log("\nDers_Havuz_Iliskisi Schema:")
cursor.execute("PRAGMA table_info(Ders_Havuz_Iliskisi)")
for row in cursor.fetchall():
    log(f"  {row}")

# Check how many pool relationships exist for Makine courses
log("\nPool relationships for 'Makine' courses:")
cursor.execute("""
    SELECT dhi.ders_adi, dhi.ders_instance, dhi.havuz_kodu, d.ders_kodu
    FROM Ders_Havuz_Iliskisi dhi
    LEFT JOIN Dersler d ON dhi.ders_adi = d.ders_adi AND dhi.ders_instance = d.ders_instance
    WHERE dhi.ders_adi LIKE '%Makine%'
    ORDER BY dhi.ders_adi, dhi.havuz_kodu
""")
results = cursor.fetchall()
log(f"Found {len(results)} pool relationships:")
for row in results:
    log(f"  {row}")

# Check current get_all_courses query output for Makine courses
log("\nCurrent get_all_courses output for 'Makine' courses:")
cursor.execute("""
    SELECT dp.ders_adi, o.ad || ' ' || o.soyad, dp.gun, dp.baslangic, dp.bitis, d.ders_kodu,
           GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf')
    FROM Ders_Programi dp
    JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
    JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
    WHERE dp.ders_adi LIKE '%Makine%'
    GROUP BY dp.program_id, dp.ders_adi, o.ad, o.soyad, dp.gun, dp.baslangic, dp.bitis, d.ders_kodu
    ORDER BY dp.gun, dp.baslangic
""")
results = cursor.fetchall()
log(f"Found {len(results)} schedule entries:")
for row in results:
    ders, hoca, gun, baslangic, bitis, kodu, siniflar = row
    log(f"  [{kodu}] {ders} - {hoca} ({gun} {baslangic}-{bitis}) [{siniflar}]")

# ========== ISSUE 2: Calendar Time Slots ==========
log("\n" + "=" * 100)
log("ISSUE 2: Calendar View Time Slots and Duplicates")
log("=" * 100)

# Check for potential duplicate entries
log("\nChecking for duplicate 'Makine' course entries in Ders_Programi:")
cursor.execute("""
    SELECT dp.program_id, dp.ders_adi, dp.ders_instance, dp.gun, dp.baslangic, dp.bitis, 
           d.ders_kodu, dp.ders_tipi, dp.ogretmen_id, dp.derslik_id
    FROM Ders_Programi dp
    JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    WHERE dp.ders_adi LIKE '%Makine%'
    ORDER BY dp.gun, dp.baslangic, dp.ders_instance
""")
results = cursor.fetchall()
log(f"Found {len(results)} schedule entries in Ders_Programi:")
for row in results:
    log(f"  {row}")

# Check what students see for Bilgisayar 3. Sınıf
log("\nSchedule for Bilgisayar Mühendisliği 3. Sınıf (including Makine courses):")
cursor.execute("""
    SELECT dp.gun, dp.baslangic, dp.bitis, dp.ders_adi,
           (SELECT ad || ' ' || soyad FROM Ogretmenler WHERE ogretmen_num = dp.ogretmen_id) as hoca,
           (SELECT derslik_adi FROM Derslikler WHERE derslik_num = dp.derslik_id) as oda,
           d.ders_kodu, dp.ders_tipi, dp.ders_instance
    FROM Ders_Programi dp
    JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    JOIN Bolumler b ON od.bolum_num = b.bolum_id
    WHERE b.bolum_adi LIKE '%Bilgisayar%' AND od.sinif_duzeyi = 3
      AND dp.ders_adi LIKE '%Makine%'
    ORDER BY dp.gun, dp.baslangic
""")
results = cursor.fetchall()
log(f"\nFound {len(results)} Makine courses for CS 3rd year:")
for row in results:
    gun, start, end, ders, hoca, oda, kod, tip, instance = row
    log(f"  [{kod}] {ders} (instance={instance}, tip={tip}) - {gun} {start}-{end} - {hoca} - {oda}")

# Check Dersler table for Makine courses
log("\nDersler table entries for 'Makine' courses:")
cursor.execute("""
    SELECT ders_kodu, ders_adi, ders_instance, bolum_num, sinif, donem, lab_saati
    FROM Dersler
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_kodu, ders_instance
""")
results = cursor.fetchall()
log(f"Found {len(results)} entries:")
for row in results:
    log(f"  {row}")

conn.close()
output_file.close()

print("\n" + "=" * 100)
print("Investigation complete! Results written to: investigation_results.txt")
print("=" * 100)
