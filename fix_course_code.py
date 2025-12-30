# -*- coding: utf-8 -*-
"""
Fix course code: Change SDIa to CSE301 for Makine Öğrenmesi
"""
import sqlite3
import shutil
from datetime import datetime

# Backup first
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_path = f"okul_veritabani.db.backup_code_fix_{timestamp}"
shutil.copy2('okul_veritabani.db', backup_path)
print(f"✅ Backup: {backup_path}")

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

print("\nBEFORE:")
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine Öğrenmesi%'
    ORDER BY ders_kodu
""")
for row in c.fetchall():
    print(f"  [{row[0]}] {row[1]} (instance={row[2]})")

# Update SDIa to CSE301
c.execute("""
    UPDATE Dersler
    SET ders_kodu = 'CSE301'
    WHERE ders_kodu = 'SDIa' 
    AND ders_adi LIKE '%Makine Öğrenmesi%'
""")

updated = c.rowcount
conn.commit()

print(f"\n✓ Updated {updated} record(s)")

print("\nAFTER:")
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine Öğrenmesi%'
    ORDER BY ders_kodu
""")
for row in c.fetchall():
    print(f"  [{row[0]}] {row[1]} (instance={row[2]})")

conn.close()
print("\n✅ Done! Restart the app to see changes.")
