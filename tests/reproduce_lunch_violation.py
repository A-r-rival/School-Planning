
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.append(PROJECT_ROOT)

from controllers.scheduler import ORToolsScheduler

def reproduce():
    # Mock Model
    mock_model = MagicMock()
    # Mock rooms: id, name, type, capacity, floor
    mock_model.aktif_derslikleri_getir.return_value = [
        (1, "Room 1", "Derslik", 50, 1) # ID=1
    ]
    mock_model.get_all_teachers_with_ids.return_value = []
    mock_model.get_course_faculty_map.return_value = {}
    mock_model.get_all_teacher_day_spans.return_value = []

    # Init Scheduler
    scheduler = ORToolsScheduler(mock_model)
    
    # Mock Data Loading
    scheduler.rooms = mock_model.aktif_derslikleri_getir()
    scheduler.teachers = []
    
    # Define Time Slots (Standard)
    # 08:30, 09:25, 10:20, 11:15(3), [Lunch 12-13], 13:00(4), ...
    scheduler.time_slots = []
    days = ["Pazartesi"]
    slot_times = [
        ("08:30", "09:15"), ("09:25", "10:10"), ("10:20", "11:05"), ("11:15", "12:00"), # 0, 1, 2, 3
        ("13:00", "13:45"), ("13:55", "14:40"), ("14:50", "15:35"), ("15:45", "16:30"), ("16:40", "17:25") # 4, 5, 6, 7, 8
    ]
    SLOTS_PER_DAY = 9
    
    def to_minutes(time_str):
        h, m = map(int, time_str.split(':'))
        return h * 60 + m

    for d_idx, day in enumerate(days):
        for s_idx, (start, end) in enumerate(slot_times):
            scheduler.time_slots.append({
                'id': s_idx,
                'day': day,
                'day_idx': d_idx,
                'slot_idx': s_idx,
                'start_str': start,
                'end_str': end,
                'start_min': to_minutes(start),
                'end_min': to_minutes(end)
            })

    # Manual Course: Duration 2
    # We want to check if we can schedule it starting at Slot 3 (11:15).
    # If Start=3, Duration=2 -> Occupies Slot 3 (11:15-12:00) and Slot 4 (13:00-13:45).
    # This bridges the lunch gap (12:00-13:00).
    scheduler.courses = [{
        'name': "Bridging Course",
        'code': "TEST101",
        'duration': 2,
        'group_ids': {1},
        'teacher_ids': {1},
        'fixed_room': None,
        'type': "Teori",
        'instance': 1,
        'program_contexts': []
    }]
    
    # Create Variables
    scheduler.cp_model = scheduler.solver # Hack: ORToolsScheduler uses .cp_model but in __init__ it sets .solver = cp_model.CpSolver(). Wait.
    # scheduler.py __init__:
    # self.cp_model = None
    # self.solver = cp_model.CpSolver()
    # It seems logic is slightly mixed in init. Let's fix up.
    from ortools.sat.python import cp_model
    scheduler.cp_model = cp_model.CpModel()
    scheduler.solver = cp_model.CpSolver()
    
    scheduler.create_variables()
    
    # Check if a start variable exists for Slot 3
    # Key: (c_idx, r_id, s_id) -> (0, 1, 3)
    start_var_3 = scheduler.starts.get((0, 1, 3))
    
    if start_var_3 is not None:
        print("Violation Possible: Variable for Start@Slot3 (Bridging Lunch) EXISTS.")
        
        # Try to force it to Start@Slot3 and solve
        scheduler.cp_model.Add(start_var_3 == 1)
        
        status = scheduler.solver.Solve(scheduler.cp_model)
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print("VIOLATION CONFIRMED: Scheduler successfully scheduled the course bridging lunch!")
        else:
            print("Bounded, but NOT Solvable (Maybe other constraints?).")
    else:
        print("Good News: Variable for Start@Slot3 does NOT exist.")

if __name__ == "__main__":
    reproduce()
