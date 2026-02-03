# -*- coding: utf-8 -*-
"""
Targeted fix for Makine Öğrenmesi duplication
"""
import sqlite3
import shutil
from datetime import datetime

# Create backup
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"okul_veritabani.db.backup_manual_{timestamp}"
shutil.copy2('okul_veritabani.db', backup_path)
print(f"Backup created: {backup_path}")

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

print("\nBEFORE:")
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine Öğrenmesi%'
    ORDER BY ders_instance
""")
for row in c.fetchall():
    print(f"  [{row[0]}] {row[1]} (instance={row[2]})")

# Check which instances exist
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine Öğrenmesi%'
    ORDER BY ders_instance
""")
courses = c.fetchall()

if len(courses) <= 1:
    print("\nNo duplication found - already fixed!")
    conn.close()
    exit(0)

print(f"\nFound {len(courses)} entries - will consolidate to CSE301")

# Keep CSE301, merge SDIa into it
primary_code = 'CSE301'
primary_name = None
primary_instance = None

# Find primary instance
for code, name, instance in courses:
    if code == primary_code:
        primary_name = name
        primary_instance = instance
        break

if not primary_instance:
    # CSE301 not found, use first instance
    primary_code, primary_name, primary_instance = courses[0]
    print(f"  Warning: CSE301 not found, using {primary_code}")

print(f"\nPrimary: [{primary_code}] {primary_name} (instance={primary_instance})")
print("Merging:")

for code, name, instance in courses:
    if instance == primary_instance:
        continue
    
    print(f"  [{code}] {name} (instance={instance}) → {primary_instance}")
    
    # Update Ders_Programi
    c.execute("""
        UPDATE Ders_Programi
        SET ders_instance = ?, ders_adi = ?
        WHERE ders_adi = ? AND ders_instance = ?
    """, (primary_instance, primary_name, name, instance))
    print(f"    Updated {c.rowcount} schedule entries")
    
    # Update Ders_Havuz_Iliskisi
    c.execute("""
        UPDATE Ders_Havuz_Iliskisi
        SET ders_instance = ?, ders_adi = ?
        WHERE ders_adi = ? AND ders_instance = ?
    """, (primary_instance, primary_name, name, instance))
    print(f"    Updated {c.rowcount} pool relationships")
    
    # Update Ders_Sinif_Iliskisi
    c.execute("""
        UPDATE Ders_Sinif_Iliskisi
        SET ders_instance = ?, ders_adi = ?
        WHERE ders_adi = ? AND ders_instance = ?
    """, (primary_instance, primary_name, name, instance))
    print(f"    Updated {c.rowcount} class relationships")
    
    # Delete duplicate
    c.execute("""
        DELETE FROM Dersler
        WHERE ders_adi = ? AND ders_instance = ?
    """, (name, instance))
    print(f"    Deleted duplicate Dersler entry")

conn.commit()

print("\nAFTER:")
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine Öğrenmesi%'
    ORDER BY ders_instance
""")
for row in c.fetchall():
    print(f"  [{row[0]}] {row[1]} (instance={row[2]})")

print("\nCS 3rd year now sees:")
c.execute("""
    SELECT DISTINCT d.ders_kodu, d.ders_adi
    FROM Ders_Programi dp
    JOIN Dersler d ON d.ders_adi = dp.ders_adi AND d.ders_instance = dp.ders_instance
    JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    JOIN Bolumler b ON od.bolum_num = b.bolum_id
    WHERE b.bolum_adi LIKE '%Bilgisayar%'
      AND od.sinif_duzeyi = 3
      AND d.ders_adi LIKE '%Makine Öğrenmesi%'
""")
count = 0
for row in c.fetchall():
    count += 1
    print(f"  [{row[0]}] {row[1]}")

if count == 1:
    print("\n✅ SUCCESS - Now showing 1 course!")
else:
    print(f"\n⚠️ Still showing {count} courses")

conn.close()
