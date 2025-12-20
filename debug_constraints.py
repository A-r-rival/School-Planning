
import sys
import os
import sqlite3
from collections import defaultdict

# Add current directory to path
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

from models.schedule_model import ScheduleModel

def analyze_constraints():
    print("Analyzing Scheduling Constraints...")
    model = ScheduleModel()
    
    # 1. Fetch all courses with details
    query = '''
        SELECT 
            d.ders_adi, 
            d.ders_instance, 
            d.teori_odasi, 
            d.lab_odasi,
            doi.ogretmen_id,
            o.ad || ' ' || o.soyad as ogretmen_adi,
            dsi.donem_sinif_num,
            b.bolum_adi,
            od.sinif_duzeyi
        FROM Dersler d
        LEFT JOIN Ders_Ogretmen_Iliskisi doi ON d.ders_adi = doi.ders_adi AND d.ders_instance = doi.ders_instance
        LEFT JOIN Ogretmenler o ON doi.ogretmen_id = o.ogretmen_num
        LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance
        LEFT JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
        LEFT JOIN Bolumler b ON od.bolum_num = b.bolum_id
    '''
    model.c.execute(query)
    courses = model.c.fetchall()
    
    print(f"Total Courses to Schedule: {len(courses)}")
    
    # 2. Analyze Teacher Load
    print("\n--- Teacher Load Analysis ---")
    teacher_load = defaultdict(int)
    for c in courses:
        teacher_name = c[5] if c[5] else "Unknown"
        teacher_load[teacher_name] += 1
        
    sorted_teachers = sorted(teacher_load.items(), key=lambda x: x[1], reverse=True)
    overloaded_teachers = [t for t in sorted_teachers if t[1] > 40]
    
    if overloaded_teachers:
        print(f"WARNING: Found {len(overloaded_teachers)} teachers with > 40 hours!")
        for t, load in overloaded_teachers:
            print(f"  - {t}: {load} hours")
    else:
        print("No teachers with > 40 hours found. Max load:", sorted_teachers[0] if sorted_teachers else "None")

    # 3. Analyze Student Group Load
    print("\n--- Student Group Load Analysis ---")
    group_load = defaultdict(int)
    for c in courses:
        if c[7] and c[8]: # Bolum adi and Sinif duzeyi
            group_name = f"{c[7]} - Year {c[8]}"
            group_load[group_name] += 1
            
    # 3. Analyze Student Group Load
    print("\n--- Student Group Load Analysis ---")
    group_load = defaultdict(int)
    for c in courses:
        # group_id is at index 6 (donem_sinif_num)
        # but let's use the readable name we constructed if available
        # tuple index 7 is bolum_adi, 8 is sinif_duzeyi
        if c[7] and c[8]: 
            group_name = f"{c[7]} - Sınıf {c[8]}"
            group_load[group_name] += 1
            
    sorted_groups = sorted(group_load.items(), key=lambda x: x[1], reverse=True)
    
    # Check for > 40
    overloaded = False
    for g, load in sorted_groups:
        if load > 40:
            print(f"CRITICAL: Student Group '{g}' has {load} hours! (Max 40)")
            overloaded = True
        elif load > 35:
            print(f"WARNING: Student Group '{g}' has {load} hours.")
            
    # 6. Deep Dive into Fixed Rooms
    print("\n--- Deep Dive: Fixed Room Validation ---")
    active_rooms = model.aktif_derslikleri_getir()
    active_room_ids = {r[0] for r in active_rooms}
    
    room_conflicts = []
    
    for c in courses:
        # Check both theory and lab rooms
        # c indexes: 2=teori_odasi, 3=lab_odasi
        fixed_rooms = []
        if c[2]: fixed_rooms.append(('Teori', c[2]))
        if c[3]: fixed_rooms.append(('Lab', c[3]))
        
        for r_type, r_id in fixed_rooms:
            if r_id not in active_room_ids:
                print(f"CRITICAL: Course '{c[0]}' assigned to INACTIVE/INVALID Room ID {r_id} ({r_type})")
                room_conflicts.append(c)
                
    if not room_conflicts:
        print("All fixed room assignments reference valid, active rooms.")
        
    print("\n--- Deep Dive: Full Capacity Room Conflicts ---")
    full_capacity_rooms = [r_id for r_id, load in fixed_room_load.items() if load >= 40]
    
    for r_id in full_capacity_rooms:
        r_name = room_map.get(r_id, f"ID {r_id}")
        print(f"\nAnalyzing Full Capacity Room: {r_name}")
        
        # Get all courses in this room
        courses_in_room = [c for c in courses if c[2] == r_id or c[3] == r_id]
        teachers_in_room = list(set([c[5] for c in courses_in_room])) # Teacher names
        teacher_ids_in_room = list(set([c[4] for c in courses_in_room])) # Teacher IDs
        
        print(f"Teachers in this room: {teachers_in_room}")
        
        # Check Unavailability for these teachers
        for t_id in teacher_ids_in_room:
            if not t_id: continue
            unavail = model.get_teacher_unavailability(t_id)
            if unavail:
                print(f"  CONFLICT: Teacher ID {t_id} has {len(unavail)} unavailability blocks!")
                for u in unavail:
                    print(f"    - {u}")
                    
        # Check if these teachers have courses in OTHER rooms
        for t_id in teacher_ids_in_room:
             if not t_id: continue
             other_courses = [c for c in courses if c[4] == t_id and (c[2] != r_id and c[3] != r_id)]
             if other_courses:
                 print(f"  CONFLICT: Teacher ID {t_id} also teaches {len(other_courses)} courses in OTHER rooms:")
                 # Since this room is 100% full, the teacher MUST be here 100% of the time (if they taught all 40 hours).
                 # If they are only teaching some hours here, we need to check intersection.
                 pass

    print("\nConstraints Analysis Complete.")

if __name__ == "__main__":
    analyze_constraints()
