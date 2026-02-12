
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from controllers.scheduler import ORToolsScheduler

print("Initializing Mock Model...")
mock_model = MagicMock()

print("Initializing Scheduler...")
# Pas None instead of mock_model to see if Mock causes issues
scheduler = ORToolsScheduler(None)

# Manually populate data
scheduler.courses = [
    {'name': 'Math', 'instance': 1, 'duration': 2, 'type': 'Teori', 'fixed_room': None, 'teacher_ids': [1], 'group_ids': [1], 'program_contexts': []},
    {'name': 'Physics', 'instance': 1, 'duration': 4, 'type': 'Lab', 'fixed_room': None, 'teacher_ids': [2], 'group_ids': [1], 'program_contexts': []}
]
scheduler.rooms = [
    (1, "Room 101", "Derslik"),
    (2, "Lab 1", "Laboratuvar")
]
scheduler.time_slots = []
for day in ['Pazartesi', 'Salı']:
    for i in range(9):
        scheduler.time_slots.append({'id': len(scheduler.time_slots), 'day': day, 'hour': i})

scheduler.teachers = [
    (1, "Teacher A", "Surname A"),
    (2, "Teacher B", "Surname B")
]

print(f"Data Set: {len(scheduler.courses)} courses, {len(scheduler.rooms)} rooms, {len(scheduler.time_slots)} slots.")

print("Running solve()...")
# We need to bypass load_data() which calls DB
# But solve() calls load_data(). 
# We can mock load_data method on the instance.
scheduler.load_data = MagicMock()

try:
    success = scheduler.solve()
    print(f"Solve returned: {success}")
except Exception as e:
    print(f"CRASH in test: {e}")
    import traceback
    traceback.print_exc()

print("Done.")
