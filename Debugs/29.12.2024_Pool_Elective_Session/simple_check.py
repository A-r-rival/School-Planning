import sqlite3

conn = sqlite3.connect('school_schedule.db')
cursor = conn.cursor()

print("Checking courses for Enerji Bilimi (dept 101), Year 4...")

try:
    cursor.execute("""
        SELECT COUNT(*) FROM Ders_Programi 
        WHERE bolum_num = 101 AND sinif_yili = 4
    """)
    total = cursor.fetchone()[0]
    print(f"Total courses: {total}")
    
    cursor.execute("""
        SELECT COUNT(*) FROM Ders_Programi 
        WHERE bolum_num = 101 AND sinif_yili = 4 
        AND (ders_tipi LIKE '%seçmeli%' OR ders_tipi LIKE '%Seçmeli%')
    """)
    electives = cursor.fetchone()[0]
    print(f"Elective courses: {electives}")
    
    if electives == 0:
        print("\n❌ NO ELECTIVE COURSES - this is why checkboxes don't work!")
except Exception as e:
    print(f"Error: {e}")

conn.close()
