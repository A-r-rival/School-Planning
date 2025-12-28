import sqlite3

conn = sqlite3.connect('school_schedule.db')
cursor = conn.cursor()

# Check for Enerji Bilimi (dept 101), Year 4
print("=== Checking Enerji Bilimi ve Teknolojileri, Year 4 ===\n")

# Get all courses for dept 101, year 4
cursor.execute("""
    SELECT ders_kodu, ders_adi, ogretmen, gun, baslangic, bitis, ders_tipi
    FROM Ders_Programi
    WHERE bolum_num = 101 AND sinif_yili = 4
    ORDER BY gun, baslangic
""")

courses = cursor.fetchall()

print(f"Total courses: {len(courses)}\n")

electives = []
mandatory = []

for code, name, teacher, day, start, end, dtype in courses:
    if dtype and "seçmeli" in dtype.lower():
        electives.append((code, name, day, start))
    else:
        mandatory.append((code, name, day, start))

print(f"Mandatory courses: {len(mandatory)}")
print(f"Elective courses: {len(electives)}\n")

if electives:
    print("=== ELECTIVE COURSES ===")
    for code, name, day, start in electives:
        print(f"  {code} - {name} ({day} {start})")
else:
    print("❌ NO ELECTIVE COURSES FOUND!")
    print("\nThis is why checkboxes don't change anything.")
    print("Need to add test elective courses to database.")

conn.close()
