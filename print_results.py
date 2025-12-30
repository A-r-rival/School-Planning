# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

print("=" * 80)
print("MAKINE COURSES - POOL RELATIONSHIPS")
print("=" * 80)

c.execute("""
    SELECT ders_adi, ders_instance, havuz_kodu
    FROM Ders_Havuz_Iliskisi
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_adi, havuz_kodu
    LIMIT 10
""")

for row in c.fetchall():
    print(f"Course: {row[0]}, Instance: {row[1]}, Pool: {row[2]}")

print("\n" + "=" * 80)
print("MAKINE COURSES - SCHEDULE")
print("=" * 80)

c.execute("""
    SELECT program_id, ders_adi, ders_instance, gun, baslangic, bitis
    FROM Ders_Programi
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY gun, baslangic
    LIMIT 10
""")

for row in c.fetchall():
    print(f"ID: {row[0]}, Course: {row[1]}, Instance: {row[2]}")
    print(f"  Time: {row[3]} {row[4]}-{row[5]}")

print("\n" + "=" * 80)
print("MAKINE COURSES - CODES")
print("=" * 80)

c.execute("""
    SELECT ders_kodu, ders_adi, ders_instance
    FROM Dersler
    WHERE ders_adi LIKE '%Makine%'
    ORDER BY ders_kodu
    LIMIT 10
""")

for row in c.fetchall():
    print(f"Code: {row[0]}, Course: {row[1]}, Instance: {row[2]}")

conn.close()
