# -*- coding: utf-8 -*-
"""
Post-migration verification
"""
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

print("=" * 80)
print("POST-MIGRATION VERIFICATION")
print("=" * 80)

# 1. Check for duplicates
print("\n1. CHECKING FOR DUPLICATE COURSES:")
c.execute("""
    SELECT ders_adi, COUNT(*) as count, GROUP_CONCAT(ders_kodu) as codes
    FROM Dersler
    WHERE ders_adi LIKE '%Makine%'
    GROUP BY ders_adi
    ORDER BY ders_adi
""")

for row in c.fetchall():
    status = "✅" if row[1] == 1 else "⚠️"
    print(f"  {status} {row[0]}: {row[1]} entry(ies) - Codes: {row[2]}")

# 2. Pool relationships
print("\n2. POOL RELATIONSHIPS:")
c.execute("""
    SELECT d.ders_kodu, d.ders_adi, d.ders_instance,
           GROUP_CONCAT(DISTINCT dhi.havuz_kodu) as pools
    FROM Dersler d
    LEFT JOIN Ders_Havuz_Iliskisi dhi ON d.ders_adi = dhi.ders_adi 
        AND d.ders_instance = dhi.ders_instance
    WHERE d.ders_adi LIKE '%Makine%'
    GROUP BY d.ders_kodu, d.ders_adi, d.ders_instance
""")

for row in c.fetchall():
    pools = row[3] if row[3] else "None"
    print(f"  [{row[0]}] {row[1]} (instance {row[2]})")
    print(f"    Pools: {pools}")

# 3. Schedule entries
print("\n3. SCHEDULE ENTRIES:")
c.execute("""
    SELECT d.ders_kodu, dp.gun, dp.baslangic, dp.bitis, COUNT(*) as count
    FROM Ders_Programi dp
    JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    WHERE d.ders_adi LIKE '%Makine%'
    GROUP BY d.ders_kodu, dp.gun, dp.baslangic, dp.bitis
""")

print(f"  Total unique schedule slots:")
count = 0
for row in c.fetchall():
    count += 1
    print(f"    [{row[0]}] {row[1]} {row[2]}-{row[3]} ({row[4]} entries)")

# 4. What CS 3rd year sees now
print("\n4. CS 3RD YEAR VIEW (should show only 1 Makine course):")
c.execute("""
    SELECT DISTINCT
        d.ders_kodu,
        d.ders_adi,
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

courses = c.fetchall()
if len(courses) == 1:
    print(f"  ✅ Shows {len(courses)} course entry (CORRECT)")
else:
    print(f"  ⚠️ Shows {len(courses)} course entries")

for row in courses:
    print(f"    [{row[0]}] {row[1]} - {row[2]} {row[3]}-{row[4]}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY:")
c.execute("SELECT COUNT(*) FROM Dersler WHERE ders_adi LIKE '%Makine%' GROUP BY ders_adi HAVING COUNT(*) > 1")
if c.fetchone():
    print("⚠️ Some duplicates still exist")
else:
    print("✅ Migration successful - no duplicates found!")
print("=" * 80)

conn.close()
