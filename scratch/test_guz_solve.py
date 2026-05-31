"""
Minimal solver test - Guz only, 45 second timeout.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler
from controllers.scheduler_services import CourseRole
from ortools.sat.python import cp_model as cp

try:
    print("Loading model...", flush=True)
    model = ScheduleModel()
    scheduler = ORToolsScheduler(model)

    print("Loading data for Güz...", flush=True)
    scheduler.load_data("Güz")

    core_idx = []
    elec_idx = []
    for i, c in enumerate(scheduler.courses):
        contexts = c.get('program_contexts', [])
        is_core = any(ctx.role == CourseRole.CORE for ctx in contexts)
        if is_core:
            core_idx.append(i)
        else:
            elec_idx.append(i)

    print(f"Core: {len(core_idx)}, Elective: {len(elec_idx)}", flush=True)

    scheduler.cp_model = cp.CpModel()
    scheduler.create_variables(optional_indices=elec_idx, active_indices=core_idx)

    for idx in elec_idx:
        for r_id in [r[0] for r in scheduler.rooms]:
            if (idx, r_id) in scheduler.room_vars:
                scheduler.cp_model.Add(scheduler.room_vars[(idx, r_id)] == 0)

    scheduler.soft_penalties = []
    scheduler.teacher_span_penalties = []
    scheduler.add_hard_constraints(include_teacher_unavailability=True)

    print("Solving (45s timeout)...", flush=True)
    solver = cp.CpSolver()
    solver.parameters.max_time_in_seconds = 45.0
    solver.parameters.log_search_progress = False

    t0 = time.time()
    status = solver.Solve(scheduler.cp_model)
    elapsed = time.time() - t0

    print(f"Status: {solver.StatusName(status)} in {elapsed:.1f}s", flush=True)

    if status in (cp.FEASIBLE, cp.OPTIMAL):
        print("✅ FEASIBLE - Semester filter fix works!")
    elif status == cp.INFEASIBLE:
        print("❌ INFEASIBLE - Still overconstrained")
    else:
        print(f"⏱️ {solver.StatusName(status)} - Time limit hit, not proven infeasible")

except Exception as e:
    import traceback
    print(f"ERROR: {e}", flush=True)
    traceback.print_exc()
