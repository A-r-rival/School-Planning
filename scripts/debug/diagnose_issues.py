import sqlite3
import sys

conn = sqlite3.connect('okul_veritabani.db')
cursor = conn.cursor()

print("=" * 100)
print("ISSUE 1: Pool Information for Elective Courses")
print("=" * 100)

# Check if we have the Ders_Havuz_Iliskisi table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Ders_Havuz_Iliskisi'")
if cursor.fetchone():
    print("\n✓ Ders_Havuz_Iliskisi table exists")
    
    # Check schema
    cursor.execute("PRAGMA table_info(Ders_Havuz_Iliskisi)")
    print("\nDers_Havuz_Iliskisi Schema:")
    for row in cursor.fetchall():
        print(f"  {row}")
    
    # Check for "Makine Öğrenmesi" in pool relationship table
    cursor.execute("""
        SELECT * FROM Ders_Havuz_Iliskisi 
        WHERE ders_adi LIKE '%Makine%' OR ders_kodu LIKE '%CSE%'
    """)
    print("\nMakine Öğrenmesi in Ders_Havuz_Iliskisi:")
    rows = cursor.fetchall()
    if rows:
        for row in rows:
            print(f"  {row}")
    else:
        print("  ❌ No records found!")
else:
    print("\n❌ Ders_Havuz_Iliskisi table does NOT exist!")

# Check Dersler table for Makine Öğrenmesi
print("\n" + "=" * 100)
print("Checking Dersler table:")
print("=" * 100)
cursor.execute("PRAGMA table_info(Dersler)")
print("\nDersler Schema:")
for row in cursor.fetchall():
    print(f"  {row}")

cursor.execute("SELECT * FROM Dersler WHERE ders_adi LIKE '%Makine%'")
print("\nMakine courses in Dersler:")
for row in cursor.fetchall():
    print(f"  {row}")

# Check Ders_Programi
print("\n" + "=" * 100)
print("ISSUE 2: Calendar View Time Slot Problem")
print("=" * 100)

cursor.execute("""
    SELECT ders_adi, ders_instance, gun, slot_baslangic, slot_bitis, oda
    FROM Ders_Programi 
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY gun, slot_baslangic
""")
print("\nMakine Öğrenmesi in Ders_Programi:")
for row in cursor.fetchall():
    print(f"  {row}")

# Check what CS3 students should see
print("\n" + "=" * 100)
print("Bilgisayar Mühendisliği 3. Sınıf Schedule:")
print("=" * 100)

cursor.execute("""
    SELECT DISTINCT 
        dp.ders_adi, 
        dp.ders_instance,
        dp.gun, 
        dp.slot_baslangic, 
        dp.slot_bitis,
        GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf')
    FROM Ders_Programi dp
    LEFT JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance  
    LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
    LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
    WHERE b.bolum_adi LIKE '%Bilgisayar%' AND od.sinif_duzeyi = 3
    GROUP BY dp.program_id 
    ORDER BY dp.gun, dp.slot_baslangic
""")

print("\nAll courses for Bilgisayar Müh. 3. Sınıf:")
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
