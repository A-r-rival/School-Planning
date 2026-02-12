import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.schedule_model import ScheduleModel
m = ScheduleModel()

# 1. Check distinct floor values
m.c.execute("SELECT DISTINCT floor FROM Derslikler WHERE silindi=0")
floors = [r[0] for r in m.c.fetchall()]
print(f"Distinct floor values in rooms: {floors}")

# 2. Count rooms per floor
for f in sorted(floors, key=lambda x: (x is None, x)):
    m.c.execute("SELECT COUNT(*) FROM Derslikler WHERE silindi=0 AND floor=?", (f,))
    cnt = m.c.fetchone()[0]
    print(f"  Floor {f}: {cnt} rooms")

# 3. Teachers with room requests
m.c.execute("SELECT ogretmen_num, ad, soyad, room_request FROM Ogretmenler WHERE room_request IS NOT NULL AND room_request != ''")
teachers = m.c.fetchall()
print(f"\nTeachers with room_request: {len(teachers)}")
for t in teachers:
    print(f"  ID={t[0]}: {t[1]} {t[2]} -> \"{t[3]}\"")
