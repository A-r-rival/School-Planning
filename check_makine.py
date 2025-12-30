import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
cursor = conn.cursor()

# Check Dersler table
cursor.execute('SELECT * FROM Dersler WHERE ders_adi LIKE "%Makine%"')
print('Dersler table:')
for row in cursor.fetchall():
    print(row)

# Check Ders_Programi table
cursor.execute('SELECT * FROM Ders_Programi WHERE ders_adi LIKE "%Makine%"')
print('\nDers_Programi table:')
for row in cursor.fetchall():
    print(row)

# Check table schema
cursor.execute('PRAGMA table_info(Dersler)')
print('\nDersler schema:')
for row in cursor.fetchall():
    print(row)

# Check if there's a Ders_Havuz_Iliskisi table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%Havuz%'")
print('\nPool-related tables:')
for row in cursor.fetchall():
    print(row)

conn.close()
