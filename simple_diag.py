# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
cursor = conn.cursor()

print("CHECKING POOL RELATIONSHIPS")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Ders_Havuz_Iliskisi'")
if cursor.fetchone():
    print("Table exists")
    cursor.execute("SELECT COUNT(*) FROM Ders_Havuz_Iliskisi")
    print(f"Total rows: {cursor.fetchone()[0]}")
else:
    print("Table does NOT exist")

print("\nCHECKING MAKINE SCHEDULE")
cursor.execute("""
    SELECT ders_adi, gun, slot_baslangic, slot_bitis
    FROM Ders_Programi 
    WHERE ders_adi LIKE '%Makine%'
""")
for row in cursor.fetchall():
    print(row)

conn.close()
