
# Same logic as test_scheduler_incremental.py but inside controllers/
import sys
import os
from ortools.sat.python import cp_model

# Add project root needed?
# If running from root: python controllers/test_incremental_with_import.py
# then sys.path[0] is controllers/.
# But we usually run from root.

print(f"Running in {os.getcwd()}")

class IncrementalSchedulerInController:
    # ... same class as before ...
    def __init__(self, model):
        self.db_model = model
        self.cp_model = None
        self.solver = cp_model.CpSolver()

    def create_variables(self):
        print("DEBUG: create_variables (MINIMAL).", flush=True)
        x = self.cp_model.NewBoolVar("Dummy_Var")
        self.cp_model.Add(x == 1)

    def solve(self):
        print("\n=== MINIMAL SOLVE IN CONTROLLER ===")
        self.cp_model = cp_model.CpModel()
        self.create_variables()
        self.solver = cp_model.CpSolver()
        self.solver.parameters.log_to_stdout = True 
        status = self.solver.Solve(self.cp_model)
        print(f"DEBUG: Solve returned status: {status}", flush=True)

sched = IncrementalSchedulerInController(None)
try:
    sched.solve()
except Exception as e:
    print(f"CRASH: {e}")
