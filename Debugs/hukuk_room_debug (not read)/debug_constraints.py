
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
    
    # 3. Analyze Student Group Load (MOVED UP)
    print("\n--- Student Group Load Analysis ---")
    group_load = defaultdict(int)
    for c in courses:
        # Tuple index 7 is bolum_adi, 8 is sinif_duzeyi
        if c[7] and c[8]: 
            group_name = f"{c[7]} - Sınıf {c[8]}"
            group_load[group_name] += 1
            
    sorted_groups = sorted(group_load.items(), key=lambda x: x[1], reverse=True)
    
    overloaded_group = False
    for g, load in sorted_groups:
        if load > 40:
            print(f"CRITICAL: Student Group '{g}' has {load} hours! (Max 40)")
            overloaded_group = True
        elif load > 35:
            print(f"WARNING: Student Group '{g}' has {load} hours.")
            
    if not overloaded_group:
         print(f"Max Student Group Load: {sorted_groups[0][1] if sorted_groups else 0}")

    # 2. Analyze Teacher Load
    
    # Check for > 40
    overloaded = False
    for g, load in sorted_groups:
        if load > 40:
            print(f"CRITICAL: Student Group '{g}' has {load} hours! (Max 40)")
            overloaded = True
        elif load > 35:
            print(f"WARNING: Student Group '{g}' has {load} hours.")
            
            
    # Calculate Fixed Room Load (restored)
    active_rooms = model.aktif_derslikleri_getir()
    room_map = {r[0]: r[1] for r in active_rooms}
    
    fixed_room_load = defaultdict(int)
    for c in courses:
        fixed_r = c[2] if c[2] else c[3] # theory or lab
        if fixed_r:
            fixed_room_load[fixed_r] += 1

    # 6. Deep Dive into Fixed Rooms
    print("\n--- Deep Dive: Fixed Room Validation ---")
    active_rooms = model.aktif_derslikleri_getir()
    active_room_ids = {r[0] for r in active_rooms}
    
    print("Analysis finished.")

if __name__ == "__main__":
    analyze_constraints()

if __name__ == "__main__":
    analyze_constraints()
