import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.schedule_model import ScheduleModel

m = ScheduleModel()

# Check if sabit_derslik column exists
m.c.execute("PRAGMA table_info(Dersler)")
columns = m.c.fetchall()
print("=== Dersler Table Columns ===")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Check for fixed room courses
m.c.execute("SELECT COUNT(*) FROM Dersler WHERE sabit_derslik IS NOT NULL")
fixed_count = m.c.fetchone()[0]
print(f"\n=== Fixed Room Courses: {fixed_count} ===")

if fixed_count > 0:
    m.c.execute("""
        SELECT d.ders_id, d.ders_adi, d.sabit_derslik, dr.derslik_adi 
        FROM Dersler d
        LEFT JOIN Derslikler dr ON d.sabit_derslik = dr.derslik_num
        WHERE d.sabit_derslik IS NOT NULL 
        LIMIT 20
    """)
    courses = m.c.fetchall()
    print("\nExamples:")
    for c in courses:
        print(f"  Course ID={c[0]}: {c[1]}")
        print(f"    -> Fixed Room ID={c[2]}, Name={c[3]}")
else:
    print("\nNo courses have fixed rooms assigned in the database.")
