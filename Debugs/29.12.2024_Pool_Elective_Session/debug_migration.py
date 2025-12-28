import sys
import sqlite3
sys.path.insert(0, r'd:\Git_Projects\School-Planning')

conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()

# Check 1: Do we have departments?
c.execute("SELECT COUNT(*) FROM Bolumler")
dept_count = c.fetchone()[0]
print(f"Departments in DB: {dept_count}")

if dept_count > 0:
    c.execute("SELECT bolum_num, bolum_adi FROM Bolumler LIMIT 5")
    print("\nSample departments:")
    for num, name in c.fetchall():
        print(f"  {num}: {name}")

# Check 2: Do we have courses in Dersler?
c.execute("SELECT COUNT(*) FROM Dersler")
course_count = c.fetchone()[0]
print(f"\nCourses in Dersler: {course_count}")

if course_count > 0:
    c.execute("SELECT ders_instance, ders_adi FROM Dersler LIMIT 5")
    print("\nSample courses:")
    for inst, name in c.fetchall():
        print(f"  [{inst}] {name}")

# Check 3: Check curriculum_data
from scripts.curriculum_data import DEPARTMENTS_DATA
print(f"\nDepartments in curriculum_data: {len(DEPARTMENTS_DATA)}")

print("\nSample curriculum keys:")
for i, key in enumerate(list(DEPARTMENTS_DATA.keys())[:3]):
    print(f"  {key}")
    pools = DEPARTMENTS_DATA[key].get('pool_codes', {})
    if pools:
        sample_pool = list(pools.keys())[0]
        sample_courses = pools[sample_pool][:2]
        print(f"    {sample_pool}: {', '.join(sample_courses)}")

conn.close()
