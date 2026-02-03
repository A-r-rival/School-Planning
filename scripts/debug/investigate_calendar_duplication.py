# -*- coding: utf-8 -*-
"""
Investigation: Calendar Duplication Issue
Following the investigation checklist to determine if this is a data issue or rendering bug
"""
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

print("=" * 100)
print("INVESTIGATION: Calendar Duplication Issue")
print("=" * 100)

# A. Check for duplicate schedule rows
print("\n" + "=" * 100)
print("A. DUPLICATE SCHEDULE ROWS CHECK")
print("=" * 100)
print("Query: Find duplicate (course, day, time) combinations")
print()

c.execute("""
    SELECT
        d.ders_adi,
        d.ders_kodu,
        dp.gun,
        dp.baslangic,
        dp.bitis,
        COUNT(*) AS adet
    FROM Ders_Programi dp
    JOIN Dersler d ON d.ders_adi = dp.ders_adi AND d.ders_instance = dp.ders_instance
    WHERE d.ders_adi LIKE '%Makine%'
    GROUP BY
        d.ders_adi,
        d.ders_kodu,
        dp.gun,
        dp.baslangic,
        dp.bitis
    HAVING COUNT(*) > 1
""")

duplicates = c.fetchall()
if duplicates:
    print(f"⚠️ FOUND {len(duplicates)} DUPLICATE SCHEDULE ENTRIES:")
    for row in duplicates:
        print(f"  {row}")
else:
    print("✅ No duplicate schedule rows found")

# B. Check for code mismatch (multiple Dersler entries for same course)
print("\n" + "=" * 100)
print("B. COURSE CODE MISMATCH CHECK")
print("=" * 100)
print("Query: How many Dersler entries exist for 'Makine Öğrenmesi'?")
print()

c.execute("""
    SELECT
        ders_kodu,
        ders_adi,
        ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_kodu, ders_instance
""")

courses = c.fetchall()
print(f"Found {len(courses)} course entries:")
for row in courses:
    print(f"  Code: {row[0]}, Name: {row[1]}, Instance: {row[2]}")

if len(courses) > 1:
    print("\n⚠️ DATA MODELING ISSUE DETECTED!")
    print("   Multiple course entries exist for what should be ONE course")
    print("   Correct model: ONE course → MANY pools (via Ders_Havuz_Iliskisi)")

# C. Check time integrity
print("\n" + "=" * 100)
print("C. TIME INTEGRITY CHECK")
print("=" * 100)
print("Query: Verify time ranges for Makine courses")
print()

c.execute("""
    SELECT
        d.ders_kodu,
        d.ders_adi,
        dp.gun,
        dp.baslangic,
        dp.bitis
    FROM Ders_Programi dp
    JOIN Dersler d ON d.ders_adi = dp.ders_adi AND d.ders_instance = dp.ders_instance
    WHERE d.ders_adi LIKE '%Makine%'
    ORDER BY dp.gun, dp.baslangic, d.ders_kodu
""")

times = c.fetchall()
print(f"Found {len(times)} schedule entries:")
for row in times:
    print(f"  [{row[0]}] {row[1]}")
    print(f"    {row[2]} {row[3]}-{row[4]}")

# Check for split rows
split_check = {}
for row in times:
    key = (row[0], row[1], row[2])  # code, name, day
    if key not in split_check:
        split_check[key] = []
    split_check[key].append((row[3], row[4]))

split_found = False
for key, time_ranges in split_check.items():
    if len(time_ranges) > 1:
        split_found = True
        print(f"\n⚠️ SPLIT TIME RANGES FOUND for {key[0]} {key[1]} on {key[2]}:")
        for start, end in time_ranges:
            print(f"    {start}-{end}")

if not split_found:
    print("\n✅ No split time ranges detected")

# D. What CS 3rd year actually sees
print("\n" + "=" * 100)
print("D. WHAT CS 3RD YEAR STUDENTS SEE")
print("=" * 100)

c.execute("""
    SELECT
        d.ders_kodu,
        d.ders_adi,
        d.ders_instance,
        dp.gun,
        dp.baslangic,
        dp.bitis,
        GROUP_CONCAT(DISTINCT dhi.havuz_kodu) as pools
    FROM Ders_Programi dp
    JOIN Dersler d ON d.ders_adi = dp.ders_adi AND d.ders_instance = dp.ders_instance
    JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    JOIN Bolumler b ON od.bolum_num = b.bolum_id
    LEFT JOIN Ders_Havuz_Iliskisi dhi ON d.ders_adi = dhi.ders_adi AND d.ders_instance = dhi.ders_instance
    WHERE b.bolum_adi LIKE '%Bilgisayar%'
      AND od.sinif_duzeyi = 3
      AND d.ders_adi LIKE '%Makine%'
    GROUP BY d.ders_kodu, d.ders_adi, d.ders_instance, dp.gun, dp.baslangic, dp.bitis
    ORDER BY dp.gun, dp.baslangic
""")

cs3_courses = c.fetchall()
print(f"\nCS 3rd year sees {len(cs3_courses)} Makine course entries:")
for row in cs3_courses:
    code, name, instance, day, start, end, pools = row
    pool_str = f" (Pools: {pools})" if pools else " (No pools)"
    print(f"  [{code}]{pool_str} {name} (instance={instance})")
    print(f"    {day} {start}-{end}")

# Summary
print("\n" + "=" * 100)
print("SUMMARY & DIAGNOSIS")
print("=" * 100)

if len(courses) > 1:
    print("\n🔴 ROOT CAUSE: DATA DUPLICATION")
    print(f"   {len(courses)} separate Dersler entries exist for 'Makine' courses")
    print("   Each has a different ders_kodu (SDIa, CSE301, etc.)")
    print("   Calendar is CORRECTLY showing both because both exist in DB")
    print("\n📋 RECOMMENDED FIX:")
    print("   1. Consolidate to ONE course entry in Dersler")
    print("   2. Use Ders_Havuz_Iliskisi to link to multiple pools")
    print("   3. Update calendar filter to hide non-matching pool instances")
else:
    print("\n✅ Data structure looks correct")
    print("   Issue may be in calendar rendering/filtering logic")

conn.close()
print("\n" + "=" * 100)
