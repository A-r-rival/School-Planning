
import sys
import os
from unittest.mock import MagicMock
import collections

# Add project root to path
# Assuming script is in tests/ (1 level deep from root) or using explicit path
if __name__ == "__main__":
    # If run as script
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
else:
    # Fallback
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

print(f"DEBUG: sys.path: {sys.path}")
from controllers.scheduler import ORToolsScheduler
from ortools.sat.python import cp_model

def verify_lunch_constraint():
    print("=== Verifying Lunch Constraint (30-min slots) ===")
    
    # 1. Mock Model
    mock_model = MagicMock()
    # Mock rooms: id=1
    mock_model.aktif_derslikleri_getir.return_value = [
        (1, "Room 1", "Derslik", 50, 1)
    ]
    mock_model.get_all_teachers_with_ids.return_value = []
    mock_model.get_course_faculty_map.return_value = {}
    mock_model.get_all_teacher_day_spans.return_value = []

    # 2. Init Scheduler
    # We rely on the NEW logic in __init__ and load_data (or manually init)
    # Since we modified scheduler.py, we can just instantiate it.
    scheduler = ORToolsScheduler(mock_model)
    scheduler.cp_model = cp_model.CpModel() # Re-init to be sure
    scheduler.solver = cp_model.CpSolver()

    # 3. Setup Time Slots (30-min from 08:30)
    # We can call the logic we just added? 
    # But load_data needs DB. Let's replicate the slot generation identical to the code.
    scheduler.time_slots = []
    days = ["Pazartesi"]
    
    start_hour = 8
    start_minute = 30
    scheduler.slots_per_day = 18
    
    current_id = 0
    for d_idx, day in enumerate(days):
        h, m = start_hour, start_minute
        for s_idx in range(scheduler.slots_per_day):
            start_min = h * 60 + m
            m += 30
            if m >= 60: m -= 60; h += 1
            end_min = h * 60 + m
            
            scheduler.time_slots.append({
                'id': current_id,
                'day': day,
                'day_idx': d_idx,
                'slot_idx': s_idx, 
                'start_time_string': f"{h:02d}:{m-30:02d}", # Approximate
                'end_time_string': f"{h:02d}:{m:02d}",
                'start_min': start_min,
                'end_min': end_min
            })
            current_id += 1
            
    # Verify Slot IDs for lunch
    # 11:30 is 690 min. 14:00 is 840 min.
    lunch_slots = [s['id'] for s in scheduler.time_slots if s['start_min'] >= 690 and s['end_min'] <= 840]
    print(f"Identified Lunch Slots: {lunch_slots}")
    # Expecting [6, 7, 8, 9, 10] for Day 0
    
    # 4. Create Course: Duration 5 (2.5 hours)
    # Group ID 101
    course_idx = 0
    scheduler.courses = [{
        'name': "Long Course",
        'code': "TEST101",
        'duration': 5, # 2.5 hours
        'group_ids': {101},
        'teacher_ids': {1},
        'fixed_room': None,
        'type': "Teori",
        'instance': 1,
        'program_contexts': []
    }]
    
    scheduler.rooms = [(1, "Room 1", "Derslik", 50, 1)]
    
    # Mock Metadata for Group
    scheduler.group_metadata = {101: ("Computer Eng", 4)}
    
    # 5. Create Variables
    print("Creating variables...")
    scheduler.create_variables()
    
    # 6. Add Lunch Constraint
    print("Adding lunch constraint...")
    scheduler.add_lunch_break_constraints()
    
    # 7. Test Case A: Force Start at 11:30 (Slot 6) -> Should FAIL
    # This occupies 6, 7, 8, 9, 10. (All 5 lunch slots).
    # Constraint allows max 4.
    
    # Find start var for (c=0, r=1, s=6)
    start_var_6 = scheduler.starts.get((0, 1, 6))
    if start_var_6 is None:
        print("ERROR: Start variable for Slot 6 not created (maybe filtered out?).")
        return

    # Add Test Constraint
    scheduler.cp_model.Add(start_var_6 == 1)
    
    print("Solving Case A (Force Start 11:30)...")
    status = scheduler.solver.Solve(scheduler.cp_model)
    
    if status == cp_model.INFEASIBLE:
         print("✅ PASS: Solver correctly determined INFEASIBLE (Lunch barrier worked).")
    elif status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
         print("❌ FAIL: Solver allowed the course to fill the lunch break!")
    else:
         print(f"Unknown Status: {status}")

    # 8. Test Case B: Force Start at 08:30 (Slot 0) -> Should PASS
    # Reset Model? No, just create new one for Case B to be clean.
    
    print("\n--- Re-initializing for Case B ---")
    scheduler.cp_model = cp_model.CpModel()
    scheduler.solver = cp_model.CpSolver()
    scheduler.create_variables()
    scheduler.add_lunch_break_constraints()
    
    start_var_0 = scheduler.starts.get((0, 1, 0))
    scheduler.cp_model.Add(start_var_0 == 1)
    
    print("Solving Case B (Force Start 08:30)...")
    status = scheduler.solver.Solve(scheduler.cp_model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
         print("✅ PASS: Solver allowed valid schedule (Outside lunch break).")
    else:
         print("❌ FAIL: Solver blocked valid schedule!")

if __name__ == "__main__":
    verify_lunch_constraint()
