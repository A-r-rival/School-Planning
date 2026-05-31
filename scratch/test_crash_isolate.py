"""
Minimal solve test with SolutionCallback to prevent OR-Tools access violation.
"""
import sys, os, faulthandler
faulthandler.enable()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler
from controllers.scheduler_services import CourseRole
from ortools.sat.python import cp_model as cp

print("Loading...", flush=True)
model = ScheduleModel()
scheduler = ORToolsScheduler(model)
scheduler.load_data("Guz")

core_idx = [i for i, c in enumerate(scheduler.courses)
            if any(ctx.role == CourseRole.CORE for ctx in c.get('program_contexts', []))]
elec_idx = [i for i in range(len(scheduler.courses)) if i not in set(core_idx)]

print(f"Core: {len(core_idx)}, Elective: {len(elec_idx)}", flush=True)

scheduler.cp_model = cp.CpModel()
print("Creating variables...", flush=True)
scheduler.create_variables(optional_indices=elec_idx, active_indices=core_idx)
print(f"Variables created: {len(scheduler.starts)} starts, {len(scheduler.vars)} occs", flush=True)

for idx in elec_idx:
    for r_id in [r[0] for r in scheduler.rooms]:
        if (idx, r_id) in scheduler.room_vars:
            scheduler.cp_model.Add(scheduler.room_vars[(idx, r_id)] == 0)

print("Adding hard constraints...", flush=True)
scheduler.soft_penalties = []
scheduler.teacher_span_penalties = []
scheduler.add_hard_constraints(include_teacher_unavailability=True)
print("Hard constraints done.", flush=True)

class SimplePrinter(cp.CpSolverSolutionCallback):
    def __init__(self):
        cp.CpSolverSolutionCallback.__init__(self)
        self.count = 0
    def on_solution_callback(self):
        self.count += 1
        print(f"  Solution #{self.count} found at {self.wall_time:.1f}s", flush=True)

solver = cp.CpSolver()
solver.parameters.max_time_in_seconds = 90.0
solver.parameters.log_search_progress = False

print("Calling Solve() with callback...", flush=True)
sys.stdout.flush()
try:
    cb = SimplePrinter()
    status = solver.Solve(scheduler.cp_model, cb)
    print(f"Status: {solver.StatusName(status)}", flush=True)
    if status in (cp.FEASIBLE, cp.OPTIMAL):
        print("SUCCESS: FEASIBLE!", flush=True)
    elif status == cp.INFEASIBLE:
        print("FAIL: INFEASIBLE", flush=True)
    else:
        print(f"TIMEOUT/UNKNOWN: {solver.StatusName(status)}", flush=True)
except Exception as e:
    import traceback
    print(f"Python exception: {e}", flush=True)
    traceback.print_exc()
