
import sqlite3
import os
from collections import defaultdict

# Database path
DB_PATH = os.path.join(os.getcwd(), 'okul_veritabani.db')

def check_teacher_loads():
    print(f"Connecting to database at: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Get all courses
    query = '''
        SELECT 
            d.ders_adi, 
            d.ders_instance, 
            doi.ogretmen_id,
            o.ad || ' ' || o.soyad as ogretmen_adi
        FROM Dersler d
        LEFT JOIN Ders_Ogretmen_Iliskisi doi ON d.ders_adi = doi.ders_adi AND d.ders_instance = doi.ders_instance
        LEFT JOIN Ogretmenler o ON doi.ogretmen_id = o.ogretmen_num
    '''
    c.execute(query)
    courses = c.fetchall()
    
    print(f"Total Courses: {len(courses)}")
    
    teacher_load = defaultdict(int)
    for row in courses:
        t_id = row[2]
        t_name = row[3] if row[3] else f"ID {t_id}"
        if t_id:
            teacher_load[(t_id, t_name)] += 1
            
    # Sort and Print
    sorted_teachers = sorted(teacher_load.items(), key=lambda x: x[1], reverse=True)
    
    overloaded = False
    print("\n--- Teacher Load Report ---")
    for (t_id, t_name), load in sorted_teachers:
        status = "OK"
        if load > 40: 
            status = "CRITICAL (>40h)"
            overloaded = True
        elif load > 35: 
            status = "WARNING (>35h)"
            
        if load > 30: # Only show heavy teachers
            print(f"Teacher: {t_name:30} (ID: {t_id}) | Load: {load:2} | {status}")
            
    if not overloaded:
        print("\nSUCCESS: No teacher exceeds 40 hours.")
    else:
        print("\nFAILURE: Some teachers are overloaded!")
        
    conn.close()

if __name__ == "__main__":
    check_teacher_loads()
