import sys
sys.path.append("d:/Git_Projects/School-Planning")
from utils.layout_solver import solve_layout
from ortools.sat.python import cp_model

events = [
    {'course_data': {'course': 'INF502', 'extra': '', 'start_str': '08:30', 'end_str': '10:30'}, 'start_slot': 0, 'end_slot': 4, 'base_center': 0.1},
    {'course_data': {'course': 'VWL473', 'extra': '', 'start_str': '08:30', 'end_str': '10:30'}, 'start_slot': 0, 'end_slot': 4, 'base_center': 0.2},
    {'course_data': {'course': 'MAT106', 'extra': '', 'start_str': '09:30', 'end_str': '11:30'}, 'start_slot': 2, 'end_slot': 6, 'base_center': 0.3},
    {'course_data': {'course': 'VWL471', 'extra': '', 'start_str': '09:30', 'end_str': '11:30'}, 'start_slot': 2, 'end_slot': 6, 'base_center': 0.4},
    {'course_data': {'course': 'WIN302', 'extra': '', 'start_str': '10:00', 'end_str': '11:00'}, 'start_slot': 3, 'end_slot': 5, 'base_center': 0.5},
    {'course_data': {'course': 'MAB314', 'extra': '', 'start_str': '10:30', 'end_str': '11:30'}, 'start_slot': 4, 'end_slot': 6, 'base_center': 0.6},
    {'course_data': {'course': 'CTD448', 'extra': '', 'start_str': '10:30', 'end_str': '11:30'}, 'start_slot': 4, 'end_slot': 6, 'base_center': 0.7},
    {'course_data': {'course': 'INF513', 'extra': '', 'start_str': '10:00', 'end_str': '13:00'}, 'start_slot': 3, 'end_slot': 9, 'base_center': 0.8},
]

slot_occ = {i: [] for i in range(18)}
for e in events:
    for i in range(int(e['start_slot']), int(e['end_slot'])):
        if 0 <= i < 18:
            slot_occ[i].append(e)

# Redefine solve_layout with print debugging
def solve_layout_debug(events, slot_occupants):
    model = cp_model.CpModel()
    left_vars = {}
    right_vars = {}
    var_counter = 0
    objective_terms = []
    PRECISION = 1000
    
    for slot_idx in range(18):
        occupants = slot_occupants.get(slot_idx, [])
        if not occupants: continue
        sorted_occs = sorted(occupants, key=lambda x: x['base_center'])
        K = len(sorted_occs)
        equal_share = PRECISION // K
        
        sigs = []
        for e in sorted_occs:
            sig = (e['course_data']['course'],)
            if sig not in sigs: sigs.append(sig)
            
            key = (sig, slot_idx)
            is_branch = (slot_idx >= e['start_slot'] + 2)
            if is_branch: min_w = 10
            else: min_w = max(30, int(equal_share * 0.7))
            max_w = min(PRECISION, int(equal_share * 3.0))
            
            left_vars[key] = model.NewIntVar(0, PRECISION, f'L_{sig[0]}_{slot_idx}')
            right_vars[key] = model.NewIntVar(0, PRECISION, f'R_{sig[0]}_{slot_idx}')
            model.Add(right_vars[key] >= left_vars[key] + min_w)
            model.Add(right_vars[key] <= left_vars[key] + max_w)
            print(f"Slot {slot_idx} | {sig[0]}: min_w={min_w}, max_w={max_w}, branch={is_branch}")
            
        intervals = []
        for sig in sigs:
            key = (sig, slot_idx)
            w = model.NewIntVar(0, PRECISION, f'W_{sig[0]}_{slot_idx}')
            model.Add(w == right_vars[key] - left_vars[key])
            intervals.append(model.NewIntervalVar(left_vars[key], w, right_vars[key], f'I_{sig[0]}_{slot_idx}'))
        
        # Slack
        for i in range(3):
            sw = model.NewIntVar(0, PRECISION, f'SW_{slot_idx}_{i}')
            sl = model.NewIntVar(0, PRECISION, f'SL_{slot_idx}_{i}')
            sr = model.NewIntVar(0, PRECISION, f'SR_{slot_idx}_{i}')
            model.Add(sr == sl + sw)
            intervals.append(model.NewIntervalVar(sl, sw, sr, f'SI_{slot_idx}_{i}'))
            
        model.AddNoOverlap(intervals)

    for e in events:
        sig = (e['course_data']['course'],)
        for s in range(e['start_slot'], e['end_slot'] - 1):
            kc = (sig, s)
            kn = (sig, s + 1)
            # OVERLAP
            max_left = model.NewIntVar(0, PRECISION, 'ml')
            min_right = model.NewIntVar(0, PRECISION, 'mr')
            model.AddMaxEquality(max_left, [left_vars[kc], left_vars[kn]])
            model.AddMinEquality(min_right, [right_vars[kc], right_vars[kn]])
            model.Add(max_left + 10 <= min_right)
            
            # Monotonic
            if s + 1 >= e['start_slot'] + 2:
                wc = right_vars[kc] - left_vars[kc]
                wn = right_vars[kn] - left_vars[kn]
                model.Add(wn <= wc)
                print(f"Monotonic: {sig[0]} slot {s+1} <= slot {s}")
                
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    print("STATUS:", solver.StatusName(status))
    if status == cp_model.OPTIMAL:
        for e in events:
            sig = (e['course_data']['course'],)
            for s in range(e['start_slot'], e['end_slot']):
                kc = (sig, s)
                w = solver.Value(right_vars[kc]) - solver.Value(left_vars[kc])
                print(f"{sig[0]} slot {s}: width={w}")

solve_layout_debug(events, slot_occ)
