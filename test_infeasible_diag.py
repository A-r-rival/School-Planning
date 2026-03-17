"""
Diagnostic: Find which constraint causes INFEASIBLE in Phase 1.
Tests combinations: no-floor, no-lunch, no-both.
"""
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ortools.sat.python import cp_model
from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler
from controllers.scheduler_services import CourseRole
import collections

TIMEOUT = 60.0  # seconds per test

def build_and_solve(label, skip_floor=False, skip_lunch=False, skip_student_conflicts=False):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"  skip_floor={skip_floor}, skip_lunch={skip_lunch}, skip_student_conflicts={skip_student_conflicts}")
    print('='*60)

    model = ScheduleModel()
    scheduler = ORToolsScheduler(model)
    scheduler.load_data(semester_filter="Bahar")

    core_indices, elective_indices = [], []
    for i, c in enumerate(scheduler.courses):
        is_elective = True
        contexts = c.get('program_contexts', [])
        if not contexts:
            is_elective = False
        else:
            for ctx in contexts:
                if ctx.role == CourseRole.CORE:
                    is_elective = False
                    break
        (elective_indices if is_elective else core_indices).append(i)

    print(f"  Core={len(core_indices)}, Elective={len(elective_indices)}")

    scheduler.cp_model = cp_model.CpModel()
    scheduler.create_variables(ignore_fixed_rooms=False, optional_indices=elective_indices, active_indices=core_indices)

    # Force electives OFF
    for idx in elective_indices:
        for r_id in [r[0] for r in scheduler.rooms]:
            if (idx, r_id) in scheduler.room_vars:
                scheduler.cp_model.Add(scheduler.room_vars[(idx, r_id)] == 0)

    scheduler.soft_penalties = []
    scheduler.teacher_span_penalties = []

    # Always add teacher unavailability
    scheduler.add_hard_constraints(include_teacher_unavailability=True)

    # Conditionally add lunch
    if not skip_lunch:
        # lunch already added inside add_hard_constraints; so we re-patch
        # Actually lunch is called inside add_hard_constraints already - see below
        pass  # handled via monkey-patch below

    scheduler.add_soft_constraints_consecutive()

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = TIMEOUT
    status = solver.Solve(scheduler.cp_model)
    name = solver.StatusName(status)
    print(f"  => Status: {name}")
    return name


# We need to temporarily override methods to skip them
# Save originals
from controllers import scheduler as sched_module

orig_lunch = sched_module.ORToolsScheduler.add_lunch_break_constraints
orig_floor = sched_module.ORToolsScheduler.add_teacher_room_preferences

def noop(self): 
    print("  [SKIPPED]")

print("\n>>> TEST 1: ALL constraints ON (baseline)")
r1 = build_and_solve("All ON")

print("\n>>> TEST 2: SKIP Lunch Break only")
sched_module.ORToolsScheduler.add_lunch_break_constraints = noop
r2 = build_and_solve("No Lunch")
sched_module.ORToolsScheduler.add_lunch_break_constraints = orig_lunch

print("\n>>> TEST 3: SKIP Floor/Room Preferences only")
sched_module.ORToolsScheduler.add_teacher_room_preferences = noop
r3 = build_and_solve("No Floor/Room Prefs")
sched_module.ORToolsScheduler.add_teacher_room_preferences = orig_floor

print("\n>>> TEST 4: SKIP BOTH Lunch + Floor/Room Prefs")
sched_module.ORToolsScheduler.add_lunch_break_constraints = noop
sched_module.ORToolsScheduler.add_teacher_room_preferences = noop
r4 = build_and_solve("No Lunch + No Floor/Room Prefs")
sched_module.ORToolsScheduler.add_lunch_break_constraints = orig_lunch
sched_module.ORToolsScheduler.add_teacher_room_preferences = orig_floor

print("\n\n" + "="*60)
print("SUMMARY")
print("="*60)
print(f"  All constraints ON       : {r1}")
print(f"  No Lunch                 : {r2}")
print(f"  No Floor/Room Prefs      : {r3}")
print(f"  No Lunch + No Floor/Room : {r4}")
