"""
Full solver test with semester filter fix.
Runs Phase 1 (core only) with a short timeout to verify feasibility.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler

print("=" * 60)
print("SOLVER FEASIBILITY TEST")
print("=" * 60)

model = ScheduleModel()
scheduler = ORToolsScheduler(model)

for SEMESTER in ["Güz", "Bahar"]:
    print(f"\n>>> Testing semester: {SEMESTER}")
    
    # Reset
    scheduler.courses = []
    scheduler.rooms = []
    scheduler.teachers = []
    scheduler.time_slots = []
    
    scheduler.load_data(SEMESTER)
    
    core_count = 0
    elec_count = 0
    from controllers.scheduler_services import CourseRole
    for c in scheduler.courses:
        contexts = c.get('program_contexts', [])
        is_core = any(ctx.role == CourseRole.CORE for ctx in contexts)
        if is_core:
            core_count += 1
        else:
            elec_count += 1
    
    total_demand = sum(c['duration'] for c in scheduler.courses)
    total_cap = len(scheduler.rooms) * len(scheduler.time_slots)
    
    print(f"  Courses: {len(scheduler.courses)} total ({core_count} core, {elec_count} elective)")
    print(f"  Demand: {total_demand} slots | Capacity: {total_cap} slots | Ratio: {total_demand/total_cap:.1%}")
    
    # Quick solve test - 30 sec timeout, core only
    from ortools.sat.python import cp_model as cp
    
    # Segregate
    core_idx = []
    elec_idx = []
    for i, c in enumerate(scheduler.courses):
        contexts = c.get('program_contexts', [])
        is_core = any(ctx.role == CourseRole.CORE for ctx in contexts)
        if is_core:
            core_idx.append(i)
        else:
            elec_idx.append(i)
    
    # Build Phase 1 model
    scheduler.cp_model = cp.CpModel()
    scheduler.create_variables(optional_indices=elec_idx, active_indices=core_idx)
    
    for idx in elec_idx:
        for r_id in [r[0] for r in scheduler.rooms]:
            if (idx, r_id) in scheduler.room_vars:
                scheduler.cp_model.Add(scheduler.room_vars[(idx, r_id)] == 0)
    
    scheduler.soft_penalties = []
    scheduler.teacher_span_penalties = []
    scheduler.add_hard_constraints(include_teacher_unavailability=True)
    
    # Solve with 30s timeout
    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.log_search_progress = False
    
    t0 = time.time()
    status = solver.Solve(scheduler.cp_model)
    elapsed = time.time() - t0
    
    status_name = solver.StatusName(status)
    print(f"  Phase 1 result: {status_name} in {elapsed:.1f}s")
    
    if status in (cp.FEASIBLE, cp.OPTIMAL):
        print(f"  ✅ FEASIBLE! Solver found a valid schedule for {SEMESTER}.")
    elif status == cp.INFEASIBLE:
        print(f"  ❌ INFEASIBLE — still overconstrained.")
    else:
        print(f"  ⏱️ UNKNOWN/TIMEOUT — may need more time but not infeasible.")

print("\n" + "=" * 60)
print("Test complete.")
