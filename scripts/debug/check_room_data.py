import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from models.schedule_model import ScheduleModel
m = ScheduleModel()

# 1. Teachers with room requests
m.c.execute("SELECT ogretmen_num, ad, soyad, room_request FROM Ogretmenler WHERE room_request IS NOT NULL AND room_request != ''")
teachers = m.c.fetchall()
print("=== TEACHERS WITH ROOM REQUESTS ===")
for t in teachers:
    print(f"  ID={t[0]}, Name={t[1]} {t[2]}, Request=\"{t[3]}\"")
print(f"Total: {len(teachers)}")

# 2. Rooms with floor data
rooms = m.aktif_derslikleri_getir()
print(f"\n=== ROOM FLOOR DISTRIBUTION (Total: {len(rooms)}) ===")
from collections import Counter
floor_counts = Counter(r[4] for r in rooms)
for f in sorted(floor_counts.keys(), key=lambda x: (x is None, x)):
    rnames = [r[1] for r in rooms if r[4] == f]
    print(f"  Floor {f}: {floor_counts[f]} rooms -> {', '.join(rnames[:8])}{'...' if len(rnames)>8 else ''}")

# 3. Cross-reference: For each teacher, simulate what the constraint does
print("\n=== CROSS-REFERENCE: Teacher Request vs Matching Rooms ===")
for t in teachers:
    t_id, name, surname, request = t
    req_lower = request.lower()
    
    # How many courses does this teacher have?
    m.c.execute("SELECT COUNT(*) FROM Ders_Ogretmen_Iliskisi WHERE ogretmen_id = ?", (t_id,))
    course_count = m.c.fetchone()[0]
    
    # Floor matching 
    target_floor = None
    if any(k in req_lower for k in ['zemin', 'giris', 'giri\u015f', 'kat 0', '0. kat']):
        target_floor = 0
    elif any(k in req_lower for k in ['kat 1', '1. kat']):
        target_floor = 1
    elif any(k in req_lower for k in ['kat 2', '2. kat']):
        target_floor = 2
    elif any(k in req_lower for k in ['kat 3', '3. kat']):
        target_floor = 3
    
    matched = []
    if target_floor is not None:
        matched = [r[1] for r in rooms if r[4] == target_floor]
    
    # Lab matching
    if 'lab' in req_lower:
        lab_rooms = [r[1] for r in rooms if 'lab' in r[1].lower()]
        matched = list(set(matched + lab_rooms))
    
    # Specific room name
    specific = [r[1] for r in rooms if r[1].lower() in req_lower]
    matched = list(set(matched + specific))
    
    status = "OK" if matched else "*** NO MATCH - WILL CAUSE INFEASIBILITY ***"
    print(f"\n  {name} {surname} (ID={t_id}, {course_count} courses)")
    print(f"    Request: \"{request}\"")
    if target_floor is not None:
        print(f"    Parsed Target Floor: {target_floor}")
    print(f"    Matching Rooms: {len(matched)} {status}")
    if matched:
        print(f"    Rooms: {', '.join(sorted(matched)[:10])}")
