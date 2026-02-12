
import sys
import os
from ortools.sat.python import cp_model
from typing import List, Dict, Tuple, Optional
import collections

# Constants
SLOTS_PER_DAY = 9

class IncrementalScheduler:
    def __init__(self, model):
        self.db_model = model
        self.courses = []
        self.rooms = []
        self.teachers = []
        self.time_slots = []
        
        self.cp_model = None
        self.solver = cp_model.CpSolver()
        self.vars = {}
        self.room_vars = {}
        self.starts = {}

    def create_variables(self, ignore_fixed_rooms=False, optional_indices=None, active_indices=None):
        print(f"DEBUG: Creating variables for {len(self.courses)} courses...", flush=True)
        if hasattr(self, 'cp_model') and self.cp_model:
             pass
        else:
             print("CRITICAL ERROR: CP Model is None!", flush=True)
             return

        for c_idx, course in enumerate(self.courses):
            if active_indices is not None and c_idx not in active_indices: continue
            
            duration = course['duration']
            possible_rooms = []
            
            for r in self.rooms:
                r_id = r[0]
                # Simplified check logic
                r_var = self.cp_model.NewBoolVar(f'c{c_idx}_r{r_id}')
                self.room_vars[(c_idx, r_id)] = r_var
                possible_rooms.append(r_var)

                valid_start_vars = []
                for s in self.time_slots:
                    start_id = s['id']
                    end_id = start_id + duration - 1
                    if end_id >= len(self.time_slots): continue
                    
                    start_day = start_id // SLOTS_PER_DAY
                    end_day = end_id // SLOTS_PER_DAY
                    
                    if start_day == end_day:
                        s_var = self.cp_model.NewBoolVar(f'start_c{c_idx}_r{r_id}_s{start_id}')
                        self.starts[(c_idx, r_id, start_id)] = s_var
                        valid_start_vars.append(s_var)
                
                if valid_start_vars:
                    self.cp_model.Add(sum(valid_start_vars) == r_var)
                else:
                    self.cp_model.Add(r_var == 0)

                # Connect Occupancy?
                # Simplified: Just create vars
                
            if possible_rooms:
                self.cp_model.Add(sum(possible_rooms) <= 1)

    def solve(self):
        self.cp_model = cp_model.CpModel()
        self.create_variables()
        
        print("Solving...")
        self.solver = cp_model.CpSolver()
        self.solver.parameters.log_search_progress = True
        self.solver.parameters.log_to_stdout = True
        
        status = self.solver.Solve(self.cp_model)
        print(f"Status: {self.solver.StatusName(status)}")

# Data Setup
scheduler = IncrementalScheduler(None)
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

print("Running Incremental Scheduler...")
try:
    scheduler.solve()
except Exception as e:
    print(f"CRASH: {e}")
