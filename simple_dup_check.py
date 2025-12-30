# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

output = open('duplication_investigation.txt', 'w', encoding='utf-8')

def log(msg):
    print(msg)
    output.write(msg + '\n')

log("INVESTIGATION RESULTS")
log("=" * 80)

# How many Dersler entries for Makine courses?
log("\n1. DERSLER TABLE - How many course entries?")
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_kodu
""")
courses = c.fetchall()
log(f"Found {len(courses)} entries:")
for row in courses:
    log(f"  {row}")

# What do CS 3rd year students see?
log("\n2. WHAT CS 3RD YEAR SEES:")
c.execute("""
    SELECT DISTINCT
        d.ders_kodu,
        d.ders_adi,
        d.ders_instance,
        dp.gun,
        dp.baslangic,
        dp.bitis
    FROM Ders_Programi dp
    JOIN Dersler d ON d.ders_adi = dp.ders_adi AND d.ders_instance = dp.ders_instance
    JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    JOIN Bolumler b ON od.bolum_num = b.bolum_id
    WHERE b.bolum_adi LIKE '%Bilgisayar%'
      AND od.sinif_duzeyi = 3
      AND d.ders_adi LIKE '%Makine%'
""")
cs3 = c.fetchall()
log(f"CS 3rd year sees {len(cs3)} schedule entries:")
for row in cs3:
    log(f"  {row}")

# Pool relationships
log("\n3. POOL RELATIONSHIPS:")
c.execute("""
    SELECT dhi.havuz_kodu, dhi.ders_adi, dhi.ders_instance
    FROM Ders_Havuz_Iliskisi dhi
    WHERE dhi.ders_adi LIKE '%Makine%'
    ORDER BY dhi.havuz_kodu, dhi.ders_instance
""")
pools = c.fetchall()
log(f"Found {len(pools)} pool relationships:")
for row in pools:
    log(f"  {row}")

log("\n" + "=" * 80)
log("DIAGNOSIS:")
if len(courses) > len(set(row[1] for row in courses)):
    log("🔴 DATA DUPLICATION CONFIRMED")
    log("   Multiple Dersler entries exist for the same course name")
    log("   This causes duplicate display in calendar")
else:
    log("✅ No obvious duplication in Dersler table")

conn.close()
output.close()

print("\nResults written to duplication_investigation.txt")
