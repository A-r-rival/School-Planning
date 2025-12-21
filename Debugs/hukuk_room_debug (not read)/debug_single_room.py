
import sys
import os
from collections import defaultdict
from ortools.sat.python import cp_model

current_dir = os.getcwd()
sys.path.insert(0, current_dir)

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler

def test_single_room(room_id):
    print(f"\n--- Testing Single Room ID: {room_id} ---")
    model = ScheduleModel()
    
    # Manually filter courses for this room
    model.c.execute("SELECT d.ders_adi, d.ders_instance, d.teori_odasi, d.lab_odasi, doi.ogretmen_id, dsi.donem_sinif_num FROM Dersler d LEFT JOIN Ders_Ogretmen_Iliskisi doi ON d.ders_adi = doi.ders_adi AND d.ders_instance = doi.ders_instance LEFT JOIN Ders_Sinif_Iliskisi dsi ON d.ders_adi = dsi.ders_adi AND d.ders_instance = dsi.ders_instance WHERE d.teori_odasi = ?", (room_id,))
    rows = model.c.fetchall()
    print(f"Courses in Room {room_id}: {len(rows)}")
    
    if not rows:
        print("No courses.")
        return

    # Mock Scheduler with Subset
    scheduler = ORToolsScheduler(model)
    scheduler.load_data() # Loads everything
    
    # Overwrite courses with ONLY this room's courses
    subset_courses = []
    for row in rows:
        ders_adi, instance, teori, lab, teacher_id, group_id = row
        subset_courses.append({
            'name': ders_adi,
            'instance': instance,
            'teacher_id': teacher_id,
            'group_id': group_id,
            'fixed_room': room_id,
            'duration': 1
        })
    scheduler.courses = subset_courses
    print("Scheduler rigged with subset data.")
    
    # Solve Strict
    scheduler.cp_model = cp_model.CpModel()
    scheduler.create_variables(ignore_fixed_rooms=False)
    scheduler.add_hard_constraints(include_teacher_unavailability=True)
    
    scheduler.solver.parameters.log_search_progress = False # reduce noise
    scheduler.solver.parameters.log_to_stdout = False
    
    print("  Mode: STRICT")
    status = scheduler.solver.Solve(scheduler.cp_model)
    print(f"  Status: {scheduler.solver.StatusName(status)}")
    
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
         print("  Mode: RELAXED_AVAILABILITY")
         scheduler.cp_model = cp_model.CpModel()
         scheduler.create_variables(ignore_fixed_rooms=False)
         scheduler.add_hard_constraints(include_teacher_unavailability=False)
         status = scheduler.solver.Solve(scheduler.cp_model)
         print(f"  Status: {scheduler.solver.StatusName(status)}")

if __name__ == "__main__":
    import sqlite3
    conn = sqlite3.connect('okul_veritabani.db')
    c = conn.cursor()
    
    # Get all rooms with meaningful load
    c.execute('''
        SELECT d.teori_odasi, count(*) as cnt 
        FROM Dersler d
        WHERE d.teori_odasi IS NOT NULL
        GROUP BY d.teori_odasi
        HAVING cnt >= 20
        ORDER BY cnt DESC
    ''')
    busy_rooms = c.fetchall()
    
    print(f"Testing {len(busy_rooms)} busy rooms...")
    
    for r_id, count in busy_rooms:
        print(f"Checking Room ID {r_id} (Load: {count})...")
        test_single_room(r_id) 
