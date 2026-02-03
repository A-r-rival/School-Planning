# -*- coding: utf-8 -*-
"""
1. Delete the (Seçmeli) variant
2. Investigate why manual delete doesn't work
"""
import sqlite3
import shutil
from datetime import datetime

# Backup
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"okul_veritabani.db.backup_delete_secmeli_{timestamp}"
shutil.copy2('okul_veritabani.db', backup_path)
print(f"✅ Backup: {backup_path}\n")

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

print("BEFORE - (Seçmeli) variant:")
c.execute("""
    SELECT dp.program_id, d.ders_kodu, dp.ders_adi, dp.gun, dp.baslangic, dp.bitis,
           o.ad || ' ' || o.soyad as teacher
    FROM Ders_Programi dp
    JOIN Dersler d ON dp.ders_adi = d.ders_adi AND dp.ders_instance = d.ders_instance
    JOIN Ogretmenler o ON dp.ogretmen_id = o.ogretmen_num
    WHERE dp.ders_adi LIKE '%Makine Öğrenmesi (Seçmeli)%'
""")
secmeli_schedule = c.fetchall()
for row in secmeli_schedule:
    print(f"  program_id={row[0]}: [{row[1]}] {row[2]} - {row[3]} {row[4]}-{row[5]} - {row[6]}")

if not secmeli_schedule:
    print("  (No entries found)")
else:
    # Get the ders_instance for deletion
    c.execute("""
        SELECT ders_instance, ders_adi
        FROM Dersler
        WHERE ders_adi LIKE '%Makine Öğrenmesi (Seçmeli)%'
    """)
    course_info = c.fetchone()
    
    if course_info:
        instance, name = course_info
        print(f"\nDeleting: {name} (instance={instance})")
        
        # Delete from Ders_Programi
        c.execute("""
            DELETE FROM Ders_Programi
            WHERE ders_adi = ? AND ders_instance = ?
        """, (name, instance))
        print(f"  ✓ Deleted {c.rowcount} schedule entries")
        
        # Delete from Ders_Havuz_Iliskisi
        c.execute("""
            DELETE FROM Ders_Havuz_Iliskisi
            WHERE ders_adi = ? AND ders_instance = ?
        """, (name, instance))
        print(f"  ✓ Deleted {c.rowcount} pool relationships")
        
        # Delete from Ders_Sinif_Iliskisi
        c.execute("""
            DELETE FROM Ders_Sinif_Iliskisi
            WHERE ders_adi = ? AND ders_instance = ?
        """, (name, instance))
        print(f"  ✓ Deleted {c.rowcount} class relationships")
        
        # Delete from Dersler
        c.execute("""
            DELETE FROM Dersler
            WHERE ders_adi = ? AND ders_instance = ?
        """, (name, instance))
        print(f"  ✓ Deleted course from Dersler")
        
        conn.commit()
        print("\n✅ Deletion complete!")

print("\n" + "=" * 80)
print("WHY MANUAL DELETE DOESN'T WORK - Investigation:")
print("=" * 80)

# Check the remove_course method logic
print("\n1. COURSE STRING FORMAT CHECK")
print("The remove_course() method expects format:")
print("   [CODE] Name - Teacher (Day HH:MM-HH:MM)")
print("\nActual format in list:")
print("   [CSE301] {Havuzlar: ZSD} Makine Öğrenmesi (Seçmeli) - Test Hoca Yılmaz (Pazartesi 10:00-12:00)")
print("\n⚠️ MISMATCH: The {Havuzlar: ...} part breaks the regex!")
print("   Regex expects: [CODE] Name - Teacher")
print("   But gets: [CODE] {Havuzlar: ...} Name - Teacher")
print("\n   The pool information we added causes the parse to fail!")

conn.close()
