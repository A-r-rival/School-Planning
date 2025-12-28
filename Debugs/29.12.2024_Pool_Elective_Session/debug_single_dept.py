# Debug: Try one department and see what happens
import sys
import sqlite3
sys.path.insert(0, r'd:\Git_Projects\School-Planning')

from scripts.curriculum_data import DEPARTMENTS_DATA

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Get dept map
c.execute("SELECT bolum_num, bolum_adi FROM Bolumler")
dept_map = {name: num for num, name in c.fetchall()}

print(f"DB Departments: {list(dept_map.keys())[:3]}")
print(f"Curriculum keys: {list(DEPARTMENTS_DATA.keys())[:3]}")

# Try first department
first_dept = list(DEPARTMENTS_DATA.keys())[0]
print(f"\nTrying department: {first_dept}")

if first_dept in dept_map:
    bolum_num = dept_map[first_dept]
    print(f"  Found in DB with ID: {bolum_num}")
    
    pools = DEPARTMENTS_DATA[first_dept].get('pool_codes', {})
    print(f"  Has {len(pools)} pools")
    
    if pools:
        first_pool = list(pools.keys())[0]
        courses = pools[first_pool]
        print(f"  Pool '{first_pool}' has {len(courses)} courses")
        
        # Try to find first 3 courses
        for course_name in courses[:3]:
            c.execute("SELECT ders_instance FROM Dersler WHERE ders_adi = ?", (course_name,))
            result = c.fetchone()
            print(f"    '{course_name}': {'FOUND' if result else 'NOT IN DB'}")
else:
    print(f"  NOT found in DB")

conn.close()
