import sqlite3

conn = sqlite3.connect('school_schedule.db')
cursor = conn.cursor()

# Clear existing test courses first
print("Removing old test courses...")
cursor.execute("DELETE FROM Ders_Programi WHERE ders_kodu LIKE 'TEST%'")

# Test courses for Enerji Bilimi (dept 101), Year 4
# Different pools in same time slots for testing vertical split
test_courses = [
    # Monday 09:00 - 3 different pools in SAME slot!
    ("TESTZSD1", "Test ZSD Ders 1", "Test Öğretmen 1", "Pazartesi", "09:00", "10:00", "Test-1", 101, 4, "Seçmeli"),
    ("TESTSD1", "Test SD Ders 1", "Test Öğretmen 2", "Pazartesi", "09:00", "10:00", "Test-2", 101, 4, "Seçmeli"),
    ("TESTUSD1", "Test ÜSD Ders 1", "Test Öğretmen 3", "Pazartesi", "09:00", "10:00", "Test-3", 101, 4, "Seçmeli"),
    
    # Tuesday 10:00 - 2 pools
    ("TESTZSD2", "Test ZSD Ders 2", "Test Öğretmen 4", "Salı", "10:00", "11:00", "Test-4", 101, 4, "Seçmeli"),
    ("TESTSD2", "Test SD Ders 2", "Test Öğretmen 5", "Salı", "10:00", "11:00", "Test-5", 101, 4, "Seçmeli"),
    
    # Wednesday 14:00 - Single elective (2 hours consecutive)
    ("TESTZSD3", "Test ZSD Ders 3", "Test Öğretmen 6", "Çarşamba", "14:00", "15:00", "Test-6", 101, 4, "Seçmeli"),
    ("TESTZSD3", "Test ZSD Ders 3", "Test Öğretmen 6", "Çarşamba", "15:00", "16:00", "Test-6", 101, 4, "Seçmeli"),
]

print(f"Adding {len(test_courses)} test elective courses...")

for code, name, teacher, day, start, end, room, dept, year, dtype in test_courses:
    cursor.execute("""
        INSERT INTO Ders_Programi 
        (ders_kodu, ders_adi, ogretmen, gun, baslangic, bitis, derslik, bolum_num, sinif_yili, ders_tipi)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (code, name, teacher, day, start, end, room, dept, year, dtype))
    print(f"  ✓ {code} - {name} ({day} {start})")

conn.commit()
conn.close()

print("\n✅ Test data added!")
print("\nNOW TEST:")
print("1. Restart the app")
print("2. Calendar → Öğrenci Grubu → Enerji Bilimi → Year 4")
print("3. Check ZSD checkbox → See ZSD courses (vertical split Mon 09:00)")
print("4. Check SD checkbox → See SD + ZSD courses")
print("5. Uncheck all → See no electives")
