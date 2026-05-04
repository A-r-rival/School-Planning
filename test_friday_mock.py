import sys
sys.path.append("d:/Git_Projects/School-Planning")
from utils.layout_solver import solve_layout
from ortools.sat.python import cp_model

events = [
    {'course_data': {'course': 'INF202', 'extra': '', 'start_str': '11:30', 'end_str': '15:00'}, 'start_slot': 6, 'end_slot': 13, 'base_center': 0.1},
    {'course_data': {'course': 'INF503', 'extra': '', 'start_str': '11:00', 'end_str': '13:00'}, 'start_slot': 5, 'end_slot': 9, 'base_center': 0.2},
    {'course_data': {'course': 'WIN306', 'extra': '', 'start_str': '12:00', 'end_str': '13:00'}, 'start_slot': 7, 'end_slot': 9, 'base_center': 0.3},
    {'course_data': {'course': 'BAU205', 'extra': '', 'start_str': '12:30', 'end_str': '14:30'}, 'start_slot': 8, 'end_slot': 12, 'base_center': 0.4},
    {'course_data': {'course': 'CTD464', 'extra': '', 'start_str': '13:00', 'end_str': '15:00'}, 'start_slot': 9, 'end_slot': 13, 'base_center': 0.5},
    {'course_data': {'course': 'VWL474', 'extra': '', 'start_str': '13:00', 'end_str': '14:00'}, 'start_slot': 9, 'end_slot': 11, 'base_center': 0.6},
    {'course_data': {'course': 'MEC421', 'extra': '', 'start_str': '13:30', 'end_str': '14:30'}, 'start_slot': 10, 'end_slot': 12, 'base_center': 0.7},
]

slot_occ = {i: [] for i in range(18)}
for e in events:
    for i in range(int(e['start_slot']), int(e['end_slot'])):
        if 0 <= i < 18:
            slot_occ[i].append(e)

layout = solve_layout(events, slot_occ)
if layout is None:
    print("SOLVER FAILED (INFEASIBLE)")
else:
    print("SOLVER SUCCESS")
    for sig, slots in layout.items():
        if sig[0] == 'INF202':
            print(f"{sig}:")
            for s, (l, r) in slots.items():
                print(f"  Slot {s}: {l:.2f} - {r:.2f} (w: {r-l:.2f})")
