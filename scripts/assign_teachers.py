
import sqlite3
import os
import sys
import random

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, "database"))

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
    
    # Initialize teacher hours
    teacher_hours = {tid: 0 for tid, _ in all_teachers}
    
    # Pre-fill with existing hours
    model.c.execute("""
        SELECT do.ogretmen_id, SUM(d.teori_saati + d.uygulama_saati + d.lab_saati)
        FROM Ders_Ogretmen_Iliskisi do
        JOIN Dersler d ON do.ders_adi = d.ders_adi AND do.ders_instance = d.ders_instance
        GROUP BY do.ogretmen_id
    """)
    for tid, hrs in model.c.fetchall():
        if tid in teacher_hours:
            teacher_hours[tid] = hrs or 0
    
    for course_name, instance in all_courses:
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
            
        # Get course hours
        model.c.execute("SELECT teori_saati, uygulama_saati, lab_saati FROM Dersler WHERE ders_adi=? AND ders_instance=?", (course_name, instance))
        hours_row = model.c.fetchone()
        course_hours = sum(hours_row) if hours_row else 2
        
        # Pick the teacher with the LEAST hours so far
        tid = min(teacher_hours, key=teacher_hours.get)
        
        assignments.append((course_name, instance, tid))
        teacher_hours[tid] += course_hours
        
    print(f"Creating {len(assignments)} new assignments...")
    
    for course_name, instance, tid in assignments:
        model.c.execute("""
            INSERT INTO Ders_Ogretmen_Iliskisi (ders_adi, ders_instance, ogretmen_id)
            VALUES (?, ?, ?)
        """, (course_name, instance, tid))
        
    model.conn.commit()
    print("Assignment complete. Max teacher load:", max(teacher_hours.values()), "hours.")
    model.close_connections()

if __name__ == "__main__":
    assign_teachers()
