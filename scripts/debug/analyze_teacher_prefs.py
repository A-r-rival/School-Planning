import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.schedule_model import ScheduleModel

m = ScheduleModel()

# Get teachers with room requests
m.c.execute("SELECT ogretmen_num, ad, soyad, room_request FROM Ogretmenler WHERE room_request IS NOT NULL AND room_request != ''")
teachers = m.c.fetchall()

print(f"=== TEACHER ROOM PREFERENCE BREAKDOWN ===")
print(f"Total teachers with preferences: {len(teachers)}\n")

floor_prefs = []
lab_prefs = []
specific_room_prefs = []
other_prefs = []

for t in teachers:
    t_id, name, surname, request = t
    req_lower = request.lower()
    
    # Categorize
    is_floor = any(k in req_lower for k in ['zemin', 'giriş', 'kat 0', 'kat 1', 'kat 2', 'kat 3', '0. kat', '1. kat', '2. kat', '3. kat'])
    is_lab = any(k in req_lower for k in ['lab', 'laboratuvar'])
    is_amfi = 'amfi' in req_lower
    
    # Check for specific room names (D101, D205, etc)
    has_specific = any(char.isdigit() for char in request)
    
    if is_floor:
        floor_prefs.append(t)
    elif is_lab:
        lab_prefs.append(t)
    elif is_amfi:
        other_prefs.append(('Amfi', t))
    elif has_specific:
        specific_room_prefs.append(t)
    else:
        other_prefs.append(('Unknown', t))

print(f"FLOOR preferences: {len(floor_prefs)}")
for t in floor_prefs:
    print(f"  {t[1]} {t[2]}: \"{t[3]}\"")

print(f"\nLAB preferences: {len(lab_prefs)}")
for t in lab_prefs:
    print(f"  {t[1]} {t[2]}: \"{t[3]}\"")

print(f"\nSPECIFIC ROOM preferences: {len(specific_room_prefs)}")
for t in specific_room_prefs:
    print(f"  {t[1]} {t[2]}: \"{t[3]}\"")

print(f"\nOTHER preferences: {len(other_prefs)}")
for cat, t in other_prefs:
    print(f"  [{cat}] {t[1]} {t[2]}: \"{t[3]}\"")

# Count courses per category
print(f"\n=== COURSES AFFECTED ===")
for category, teacher_list in [("Floor", floor_prefs), ("Lab", lab_prefs), ("Specific Room", specific_room_prefs)]:
    total_courses = 0
    for t in teacher_list:
        m.c.execute("SELECT COUNT(*) FROM Ders_Ogretmen_Iliskisi WHERE ogretmen_id = ?", (t[0],))
        total_courses += m.c.fetchone()[0]
    print(f"{category} preferences affect {total_courses} courses")
