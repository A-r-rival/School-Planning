import sqlite3

conn = sqlite3.connect('school_schedule.db')
c = conn.cursor()

# Count elective courses in schedule
c.execute('''
    SELECT COUNT(*) 
    FROM Ders_Programi 
    WHERE ders_adi LIKE "%Seçmeli%" OR ders_kodu LIKE "%SD%"
''')
elective_count = c.fetchone()[0]

# Sample elective courses
c.execute('''
    SELECT ders_kodu, ders_adi, gun, slot_baslangic, slot_bitis 
    FROM Ders_Programi 
    WHERE ders_adi LIKE "%Seçmeli%" OR ders_kodu LIKE "%SD%"
    LIMIT 10
''')
samples = c.fetchall()

print(f"Toplam seçmeli ders sayısı schedule'da: {elective_count}")
print("\nÖrnek seçmeli dersler:")
for row in samples:
    print(f"  [{row[0]}] {row[1]} - {row[2]} {row[3]}-{row[4]}")

conn.close()
