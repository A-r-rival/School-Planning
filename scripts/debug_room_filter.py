import sqlite3
import collections

# Load Data from DB
conn = sqlite3.connect('database/okul_veritabani.db')
c = conn.cursor()

# Get Rooms
c.execute("SELECT derslik_num, derslik_adi, derslik_tipi, kapasite FROM Derslikler")
rooms = c.fetchall()
print(f"Loaded {len(rooms)} rooms.")

# Instead of querying by DB ID (since the solver logs use array c_idx), 
# let's just query all courses and test the first 10 that fail.
c.execute('''
    SELECT d.ders_instance, d.ders_adi, d.teori_saati, d.uygulama_saati, d.lab_saati, ds.teori_odasi
    FROM Dersler d
    LEFT JOIN Dersler ds ON d.ders_instance = ds.ders_instance AND d.ders_adi = ds.ders_adi
''')
test_courses = c.fetchall()

tested_failures = 0
for row in test_courses:
    c_id, c_name, t, u, l, fixed_room = row
    
    # Determine basic type like builder.py does
    c_type = "Teori"
    if l > t and l > u:
        c_type = "Lab"
    elif u > t and u > l:
        c_type = "Uygulama"
        
    print(f"\n--- Testing Course: {c_name} (ID: {c_id}) ---")
    print(f"Type: {c_type} (T:{t}, U:{u}, L:{l}) | Fixed Room: {fixed_room}")
    
    viable = 0
    reasons = collections.defaultdict(int)
    
    is_lab_course = "lab" in c_type.lower()
    
    for r in rooms:
        r_id, r_name, r_type, caps = r
        r_type_str = str(r_type).lower() if r_type else ""
        r_name_str = str(r_name).lower() if r_name else ""
        
        # 1. FIXED ROOM FILTER
        if fixed_room and fixed_room != r_id:
            reasons["Fixed Room Mismatch"] += 1
            continue
            
        # 2. ROOM TYPE LOGIC (from scheduler.py)
        is_lab_keywords = ["laboratuvar", "lab"]
        is_lab_room = any(k in r_name_str for k in is_lab_keywords) or \
                      any(k in r_type_str for k in is_lab_keywords)
        is_amfi = "amfi" in r_name_str or "amfi" in r_type_str
        
        # Rule A: Lab Courses -> ONLY in Lab Rooms, NEVER in Amfi
        if is_lab_course:
            if not is_lab_room:
                reasons["Lab Course not in Lab Room"] += 1
                continue
            if is_amfi:
                reasons["Lab Course in Amfi"] += 1
                continue
                
        # Rule B: Non-Lab Courses -> NEVER in Lab Rooms
        else:
            if is_lab_room:
                reasons["Theory Course in Lab Room"] += 1
                continue
                
        viable += 1
        
    if viable == 0:
        print(f"\n--- Testing Course: {c_name} (Instance: {c_id}) ---")
        print(f"Type: {c_type} (T:{t}, U:{u}, L:{l}) | Fixed Room: {fixed_room}")
        print("  Rejection Reasons:")
        for reason, count in reasons.items():
            print(f"    - {reason}: {count} rooms")
        tested_failures += 1
        if tested_failures >= 10:
            break

conn.close()
