# -*- coding: utf-8 -*-
"""
New simplified solve() method for scheduler
"""

def solve(self):
    """Solve all courses (core + elective) in single phase with soft constraints."""
    self.load_data()
    
    # --- Pre-Solve Capacity Check ---
    total_demand = sum(c['duration'] for c in self.courses)
    total_capacity = len(self.rooms) * len(self.time_slots)
    
    print(f"\n[DIAGNOSTIC] Capacity Check:")
    print(f"  - Total Course Hours Needed: {total_demand}")
    print(f"  - Total School Capacity (Rooms x Slots): {total_capacity}")
    
    if total_demand > total_capacity:
        print(f"CRITICAL WARNING: Demand exceeds Capacity!")
    
    # Count courses for diagnostics
    core_count = sum(1 for c in self.courses if not c.get('is_elective', False))
    elective_count = sum(1 for c in self.courses if c.get('is_elective', False))
    print(f"DEBUG: {core_count} Core, {elective_count} Elective courses")
    
    # --- SINGLE PHASE: ALL COURSES ---
    print("\n=== SOLVING ALL COURSES (Core + Elective) ===")
    
    self.cp_model = cp_model.CpModel()
    
    # Make electives optional (won't fail if don't fit)
    elective_indices = [i for i, c in enumerate(self.courses) if c.get('is_elective', False)]
    self.create_variables(ignore_fixed_rooms=False, optional_indices=elective_indices)
    
    self.add_hard_constraints(include_teacher_unavailability=True)
    self.add_soft_constraints_consecutive()
    
    # OBJECTIVE: Maximize assigned courses - penalty for pool overlaps
    all_course_vars = []
    for c_idx in range(len(self.courses)):
        for r in self.rooms:
            r_id = r[0]
            if (c_idx, r_id) in self.room_vars:
                all_course_vars.append(self.room_vars[(c_idx, r_id)])
    
    # Compute penalty for different-pool elective overlaps
    penalty_vars = []
    if hasattr(self, 'group_slot_data'):
        for (g_id, s_id), data in self.group_slot_data.items():
            pools = list(data['electives'].keys())
            
            # Penalize different pools overlapping
            for i, pool_a in enumerate(pools):
                for pool_b in pools[i+1:]:
                    vars_a = data['electives'][pool_a]
                    vars_b = data['electives'][pool_b]
                    
                    if vars_a and vars_b:
                        # Pool A active indicator
                        a_active = self.cp_model.NewBoolVar(f'penalty_g{g_id}_s{s_id}_{pool_a}')
                        self.cp_model.AddMaxEquality(a_active, vars_a)
                        
                        # Pool B active indicator
                        b_active = self.cp_model.NewBoolVar(f'penalty_g{g_id}_s{s_id}_{pool_b}')
                        self.cp_model.AddMaxEquality(b_active, vars_b)
                        
                        # Penalty if both active
                        overlap = self.cp_model.NewBoolVar(f'overlap_{g_id}_{s_id}_{pool_a}_{pool_b}')
                        self.cp_model.AddBoolAnd([a_active, b_active]).OnlyEnforceIf(overlap)
                        self.cp_model.AddBoolOr([a_active.Not(), b_active.Not()]).OnlyEnforceIf(overlap.Not())
                        
                        penalty_vars.append(overlap)
    
    # Maximize: courses placed - 10x penalty for pool overlaps
    if all_course_vars:
        objective = sum(all_course_vars)
        if penalty_vars:
            objective = objective - 10 * sum(penalty_vars)
        self.cp_model.Maximize(objective)
    
    # Solve
    if self._run_solver("SINGLE_PHASE", timeout=300.0):
        return True
    else:
        print("ERROR: Solver failed to find solution.")
        return False
