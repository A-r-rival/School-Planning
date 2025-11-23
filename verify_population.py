import sys
import os
import sqlite3

# Add project root to path
sys.path.append(os.getcwd())

from models.schedule_model import ScheduleModel

def verify():
    print("Verifying Student Population...")
    model = ScheduleModel()
    
    # 1. Check Counts
    model.c.execute("SELECT COUNT(*) FROM Ogrenciler")
    student_count = model.c.fetchone()[0]
    print(f"Total Students: {student_count}")
    
    model.c.execute("SELECT COUNT(*) FROM Ogrenci_Notlari")
    grades_count = model.c.fetchone()[0]
    print(f"Total Grades: {grades_count}")
    
    model.c.execute("SELECT COUNT(*) FROM Ders_Sinif_Iliskisi")
    enrollment_count = model.c.fetchone()[0]
    print(f"Total Class Enrollments: {enrollment_count}")

    # 2. Check a Sample Student
    model.c.execute("SELECT ogrenci_num, ad, soyad FROM Ogrenciler LIMIT 1")
    student = model.c.fetchone()
    if student:
        student_id, ad, soyad = student
        print(f"\nSample Student: {ad} {soyad} ({student_id})")
        
        # Test get_student_grades
        grades = model.get_student_grades(student_id)
        print(f"Grades (Latest): {len(grades)}")
        for g in grades[:5]:
            print(f" - {g[3]}: {g[4]} ({g[6]})")
            
        # Check Verilen_Dersler
        passed_courses = model.verilen_dersleri_getir(student_id)
        print(f"Passed Courses (String): {len(passed_courses)}")
        print(f"Sample: {passed_courses[:3]}")

    model.conn.close()

if __name__ == "__main__":
    verify()
