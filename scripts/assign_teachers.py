
import sqlite3
import os
import sys
import random

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir)) # Up one level from 'Schedule Creation v1', then one more? No, check path.
# d:\D.P. Projesi\Schedule Creation v1\populate_classrooms.py
# project root is d:\D.P. Projesi
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from models.schedule_model import ScheduleModel

def assign_teachers():
    model = ScheduleModel()
    
    # 1. Get all courses
    model.c.execute("SELECT ders_adi, ders_instance FROM Dersler")
    all_courses = model.c.fetchall()
    
    # 2. Get all teachers
    model.c.execute("SELECT ogretmen_num, bolum_adi FROM Ogretmenler")
    all_teachers = model.c.fetchall()
    
    if not all_teachers:
        print("No teachers found!")
        return
        
    teachers_by_dept = {}
    general_teachers = []
    
    for t in all_teachers:
        tid, dept = t
        if dept == "Genel":
            general_teachers.append(tid)
        else:
            if dept not in teachers_by_dept:
                teachers_by_dept[dept] = []
            teachers_by_dept[dept].append(tid)
            
    print(f"Assigning teachers for {len(all_courses)} courses...")
    
    assignments = []
    
    for course_name, instance in all_courses:
        # Try to find a teacher from the course's department
        # We need to guess department from course code or known list.
        # But 'Dersler' doesn't have department. 'Ders_Sinif_Iliskisi' connects to 'Ogrenci_Donemleri' which has 'Bolum_Num'.
        # Let's simple random for now, but try to match if possible.
        
        # Or simpler: Just Pick Random. The user asked for "randomised".
        
        # Check if already assigned
        try:
            model.c.execute("""
                SELECT ogretmen_id FROM Ders_Ogretmen_Iliskisi 
                WHERE ders_adi=? AND ders_instance=?
            """, (course_name, instance))
        except Exception as e:
            print(f"Error checking teacher: {e}")
            sys.exit(1)
        
        if model.c.fetchone():
            continue # Already has a teacher
            
        # Pick a random teacher
        tid = random.choice(all_teachers)[0]
        
        assignments.append((course_name, instance, tid))
        
    print(f"Creating {len(assignments)} new assignments...")
    
    for course_name, instance, tid in assignments:
        model.c.execute("""
            INSERT INTO Ders_Ogretmen_Iliskisi (ders_adi, ders_instance, ogretmen_id)
            VALUES (?, ?, ?)
        """, (course_name, instance, tid))
        
    model.conn.commit()
    print("Assignment complete.")
    model.close_connections()

if __name__ == "__main__":
    assign_teachers()
