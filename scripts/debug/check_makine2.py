import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
cursor = conn.cursor()

# Check Dersler table for Makine courses
print("=" * 80)
print("DERSLER TABLE - Makine courses:")
print("=" * 80)
cursor.execute('SELECT * FROM Dersler WHERE ders_adi LIKE "%Makine%"')
for row in cursor.fetchall():
    print(f"  {row}")

# Check Ders_Programi table
print("\n" + "=" * 80)
print("DERS_PROGRAMI TABLE - Makine courses:")
print("=" * 80)
cursor.execute('SELECT * FROM Ders_Programi WHERE ders_adi LIKE "%Makine%"')
for row in cursor.fetchall():
    print(f"  {row}")

# Check Ders_Havuz_Iliskisi table
print("\n" + "=" * 80)
print("DERS_HAVUZ_ILISKISI TABLE - Makine courses:")
print("=" * 80)
cursor.execute('SELECT * FROM Ders_Havuz_Iliskisi WHERE ders_adi LIKE "%Makine%"')
for row in cursor.fetchall():
    print(f"  {row}")

# Check table schemas
print("\n" + "=" * 80)
print("DERSLER SCHEMA:")
print("=" * 80)
cursor.execute('PRAGMA table_info(Dersler)')
for row in cursor.fetchall():
    print(f"  {row}")

print("\n" + "=" * 80)
print("DERS_HAVUZ_ILISKISI SCHEMA:")
print("=" * 80)
cursor.execute('PRAGMA table_info(Ders_Havuz_Iliskisi)')
for row in cursor.fetchall():
    print(f"  {row}")

conn.close()
