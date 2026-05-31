"""
Quick solver test: loads courses with semester filter and reports capacity.
Run from project root: python scratch/test_solver_capacity.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('PYTHONIOENCODING', 'utf-8')

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler

print("=== Solver Capacity Test ===")
print("Loading model...")
model = ScheduleModel()
scheduler = ORToolsScheduler(model)

SEMESTER = "Güz"
print(f"Loading data for semester: {SEMESTER}")
scheduler.load_data(SEMESTER)

print(f"\n--- Results ---")
print(f"Courses loaded: {len(scheduler.courses)}")
print(f"Time slots: {len(scheduler.time_slots)}")
print(f"Rooms: {len(scheduler.rooms)}")

if scheduler.courses:
    total_demand = sum(c['duration'] for c in scheduler.courses)
    total_capacity = len(scheduler.rooms) * len(scheduler.time_slots)
    print(f"\nTotal demand: {total_demand} slots")
    print(f"Total capacity: {total_capacity} slots")
    print(f"Ratio: {total_demand/total_capacity:.1%}")
    
    # Per-group analysis
    from collections import defaultdict
    group_load = defaultdict(int)
    for c in scheduler.courses:
        for gid in c.get('group_ids', []):
            group_load[gid] += c['duration']
    
    if group_load:
        max_gid = max(group_load, key=lambda g: group_load[g])
        max_load = group_load[max_gid]
        print(f"\nMax group load: {max_load} slots (group {max_gid})")
        print(f"Max group capacity: {len(scheduler.time_slots)} slots")
        if max_load > len(scheduler.time_slots):
            print(f"WARNING: Group {max_gid} is OVERLOADED by {max_load - len(scheduler.time_slots)} slots!")
        else:
            print(f"OK: Max group load fits in capacity.")
else:
    print("ERROR: No courses loaded!")

print("\nDone.")
