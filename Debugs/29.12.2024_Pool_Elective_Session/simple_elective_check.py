import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

c.execute("SELECT COUNT(*) FROM Ders_Programi")
total = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM Ders_Programi WHERE LOWER(ders_adi) LIKE '%seçmeli%'")
elective_count = c.fetchone()[0]

print(f"Total courses: {total}")
print(f"Elective courses (name contains 'seçmeli'): {elective_count}")
print(f"Percentage: {elective_count/total*100:.1f}%")

if elective_count > 0:
    c.execute("SELECT ders_adi FROM Ders_Programi WHERE LOWER(ders_adi) LIKE '%seçmeli%' LIMIT 5")
    print("\nSample electives:")
    for row in c.fetchall():
        print(f"  - {row[0]}")
else:
    print("\n❌ NO ELECTIVES IN DATABASE")

conn.close()
