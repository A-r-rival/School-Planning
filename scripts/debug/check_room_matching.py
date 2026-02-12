import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, errors='replace')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from models.schedule_model import ScheduleModel
m = ScheduleModel()

# Get teachers with room requests
m.c.execute("SELECT ogretmen_num, ad, soyad, room_request FROM Ogretmenler WHERE room_request IS NOT NULL AND room_request != ''")
teachers = m.c.fetchall()

# Get all active rooms with floor data
rooms = m.aktif_derslikleri_getir()

print("=== ROOM PREFERENCE MATCHING VERIFICATION ===\n")

for t in teachers:
    t_id, name, surname, request = t
    req_lower = request.lower()
    
    # How many courses does this teacher have?
    m.c.execute("SELECT COUNT(*) FROM Ders_Ogretmen_Iliskisi WHERE ogretmen_id = ?", (t_id,))
    course_count = m.c.fetchone()[0]
    
    # Simulate the matching logic from scheduler.py
    matched_rooms = []
    
    # Floor matching (from scheduler.py lines 584-591)
    target_floor = None
    if any(k in req_lower for k in ['zemin', 'giriş', 'kat 0', '0. kat']):
        target_floor = 0
    elif any(k in req_lower for k in ['kat 1', '1. kat']):
        target_floor = 1
    elif any(k in req_lower for k in ['kat 2', '2. kat']):
        target_floor = 2
    elif any(k in req_lower for k in ['kat 3', '3. kat']):
        target_floor = 3
    
    if target_floor is not None:
        for r in rooms:
            r_floor = r[4] if len(r) > 4 else 0
            if r_floor == target_floor:
                matched_rooms.append(r[1])
    
    # Lab matching
    if 'lab' in req_lower:
        for r in rooms:
            if 'lab' in r[1].lower() and r[1] not in matched_rooms:
                matched_rooms.append(r[1])
    
    # Specific room name
    for r in rooms:
        if r[1].lower() in req_lower and r[1] not in matched_rooms:
            matched_rooms.append(r[1])
    
    status = "OK" if matched_rooms else "*** ZERO MATCHES - WILL CAUSE INFEASIBILITY ***"
    print(f"{name} {surname} ({course_count} courses)")
    print(f"  Request: \"{request}\"")
    print(f"  Lowercased: \"{req_lower}\"")
    if target_floor is not None:
        print(f"  Detected Floor: {target_floor}")
    print(f"  Matching Rooms: {len(matched_rooms)} {status}")
    if matched_rooms and len(matched_rooms) <= 10:
        print(f"  Rooms: {', '.join(matched_rooms)}")
    elif matched_rooms:
        print(f"  Rooms: {', '.join(matched_rooms[:10])} ... ({len(matched_rooms)} total)")
    print()
