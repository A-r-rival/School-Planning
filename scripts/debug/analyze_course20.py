import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.schedule_model import ScheduleModel

m = ScheduleModel()

# Get Course 20 details
m.c.execute("""
    SELECT d.ders_id, d.ders_adi, d.ders_tipi, d.grup_buyuklugu, d.sube_kodu 
    FROM Dersler d 
    WHERE d.ders_id = 20
""")
course = m.c.fetchone()

print("=== COURSE 20 DETAILS ===")
print(f"  ID: {course[0]}")
print(f"  Name: {course[1]}")
print(f"  Type: {course[2]}")
print(f"  Group Size (Capacity Need): {course[3]}")
print(f"  Section Code: {course[4]}")

# Get teacher for this course
m.c.execute("""
    SELECT o.ogretmen_num, o.ad, o.soyad, o.room_request
    FROM Ders_Ogretmen_Iliskisi doi
    JOIN Ogretmenler o ON doi.ogretmen_id = o.ogretmen_num
    WHERE doi.ders_id = 20
""")
teachers = m.c.fetchall()
print(f"\n=== TEACHERS FOR COURSE 20 ===")
for t in teachers:
    print(f"  Teacher ID={t[0]}: {t[1]}  {t[2]}, Room Request=\"{t[3]}\"")

# Get all rooms and check which could theoretically fit this course
rooms = m.aktif_derslikleri_getir()
print(f"\n=== ROOM ANALYSIS ===")
print(f"Total active rooms: {len(rooms)}")

# Count rooms by type
course_type = course[2].lower() if course[2] else ""
is_lab_course = 'lab' in course_type
capacity_needed = course[3] or 30

print(f"\nCourse is {'LAB' if is_lab_course else 'THEORY'}")
print(f"Capacity needed: {capacity_needed}")

viable_by_type = [r for r in rooms if ('lab' in r[1].lower()) == is_lab_course]
print(f"Rooms matching type: {len(viable_by_type)}")

viable_by_capacity = [r for r in viable_by_type if r[3] >= capacity_needed]
print(f"Rooms with sufficient capacity: {len(viable_by_capacity)}")

if len(viable_by_capacity) <= 5:
    print(f"\nViable rooms:")
    for r in viable_by_capacity:
        print(f"  {r[1]} (Cap={r[3]}, Floor={r[4]}, Type={r[2]})")
