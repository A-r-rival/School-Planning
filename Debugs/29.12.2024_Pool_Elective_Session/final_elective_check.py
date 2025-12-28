import sqlite3

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

print("=" * 70)
print("DATABASE STATUS CHECK")
print("=" * 70)

# 1. Total courses
c.execute("SELECT COUNT(*) FROM Dersler")
total = c.fetchone()[0]
print(f"\n1. Total courses in Dersler: {total}")

# 2. Courses with "Seçmeli" in name
c.execute("SELECT COUNT(*) FROM Dersler WHERE LOWER(ders_adi) LIKE '%seçmeli%'")
elective_named = c.fetchone()[0]
print(f"2. Courses with 'Seçmeli' in name: {elective_named}")

# 3. Sample of these
c.execute("SELECT ders_adi FROM Dersler WHERE LOWER(ders_adi) LIKE '%seçmeli%' LIMIT 10")
print("\n   Sample elective-named courses:")
for row in c.fetchall():
    print(f"     - {row[0]}")

# 4. Check for specific known electives
known_electives = ['Yapay Zeka', 'Veri Madenciliği', 'Makine Öğrenmesi', 'Bilgisayar Ağları', 'Veritabanı']
print(f"\n3. Checking for specific elective topics:")
for name in known_electives:
    c.execute("SELECT COUNT(*) FROM Dersler WHERE LOWER(ders_adi) LIKE ?", (f'%{name.lower()}%',))
    count = c.fetchone()[0]
    status = "✅" if count > 0 else "❌"
    print(f"   {status} {name}: {count}")

conn.close()

print("\n" + "=" * 70)
print("CONCLUSION:")
print("=" * 70)
if elective_named > 0:
    print("✅ Database HAS courses with 'Seçmeli' in their names")
    print("   BUT these might be generic like 'Seçmeli Ders I/II'")
    print("   NOT specific like 'Yapay Zeka' or 'Veri Madenciliği'")
else:
    print("❌ No courses with 'Seçmeli' found")
