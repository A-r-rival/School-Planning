# -*- coding: utf-8 -*-
import sqlite3

output = open('investigation_results.txt', 'w', encoding='utf-8')

def log(msg):
    print(msg)
    output.write(msg + '\n')

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

log("=" * 100)
log("INVESTIGATION RESULTS")
log("=" * 100)

# Issue 1: Pool information
log("\n1. POOL RELATIONSHIPS FOR MAKINE COURSES:")
log("-" * 100)
c.execute("""
    SELECT ders_adi, ders_instance, havuz_kodu
    FROM Ders_Havuz_Iliskisi
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_adi, havuz_kodu
""")
rows = c.fetchall()
log(f"Found {len(rows)} pool relationships:")
for row in rows:
    log(f"  {row}")

# Issue 2: Schedule entries
log("\n2. SCHEDULE ENTRIES FOR MAKINE COURSES:")
log("-" * 100)
c.execute("""
    SELECT program_id, ders_adi,ders_instance, gun, baslangic, bitis, ogretmen_id, derslik_id, ders_tipi
    FROM Ders_Programi
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY gun, baslangic, ders_instance
""")
rows = c.fetchall()
log(f"\nFound {len(rows)} schedule entries:")
for row in rows:
    log(f"  {row}")

# Get course codes
log("\n3. COURSE CODES FOR MAKINE:")
log("-" * 100)
c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_kodu, ders_instance
""")
rows = c.fetchall()
for row in rows:
    log(f"  {row}")

conn.close()
output.close()

print("\nResults written to investigation_results.txt")
