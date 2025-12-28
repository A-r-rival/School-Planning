import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Total courses
c.execute("SELECT COUNT(*) FROM Ders_Programi")
total = c.fetchone()[0]

# Courses with "Seçmeli" in name
c.execute("SELECT COUNT(*) FROM Ders_Programi WHERE LOWER(ders_adi) LIKE '%seçmeli%'")
elective_count = c.fetchone()[0]

# Sample electives
c.execute("""
    SELECT ders_adi, gun, slot_baslangic 
    FROM Ders_Programi 
    WHERE LOWER(ders_adi) LIKE '%seçmeli%'
    LIMIT 10
""")
samples = c.fetchall()

print("=" * 60)
print("ELECTIVE COURSES IN DATABASE")
print("=" * 60)
print(f"Total courses in Ders_Programi: {total}")
print(f"Courses with 'Seçmeli' in name: {elective_count}")
print(f"Percentage: {elective_count/total*100:.1f}%")

if samples:
    print("\nSample elective courses:")
    for name, day, time in samples:
        print(f"  {name[:50]:50} | {day} {time}")
else:
    print("\n❌ NO ELECTIVES FOUND!")

conn.close()
