
import sys
import os
import time

# Add root to path
sys.path.append(os.getcwd())

def step(name, func):
    print(f"\n[STEP] {name}...")
    try:
        func()
        print(f"[STEP] {name} SUCCESS.")
    except Exception as e:
        print(f"[STEP] {name} FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def init_model():
    from models.schedule_model import ScheduleModel
    global model
    model = ScheduleModel()

def run_seeder():
    # Seeder is run in __init__ of ScheduleModel, so it's already done.
    # But let's verify data.
    model.c.execute("SELECT count(*) FROM Bolumler")
    c = model.c.fetchone()[0]
    print(f"  Bolum count: {c}")

def init_scheduler():
    from controllers.scheduler import ORToolsScheduler
    global scheduler
    scheduler = ORToolsScheduler(model)

def load_data():
    scheduler.load_data()

def create_vars():
    from ortools.sat.python import cp_model
    scheduler.cp_model = cp_model.CpModel()
    scheduler.create_variables()

def add_hard_constraints():
    scheduler.add_hard_constraints()

def add_soft_constraints():
    scheduler.add_soft_constraints_consecutive()

def run_solver():
    print("Running solver manually...")
    scheduler._run_solver("TEST_PHASE", timeout=30.0)

if __name__ == "__main__":
    step("Init Model", init_model)
    step("Run Seeder check", run_seeder)
    step("Init Scheduler", init_scheduler)
    step("Load Data", load_data)
    step("Create Variables", create_vars)
    step("Add Hard Constraints", add_hard_constraints)
    step("Add Soft Constraints", add_soft_constraints)
    step("Run Solver", run_solver)
    print("\nDONE.")
