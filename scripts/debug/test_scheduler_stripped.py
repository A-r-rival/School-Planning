
import sys
import os
from ortools.sat.python import cp_model

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

print(f"Project Root: {project_root}")

class StrippedScheduler:
    def __init__(self):
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.solver.parameters.log_search_progress = True
        self.solver.parameters.log_to_stdout = True

    def solve(self):
        print("Creating variable...")
        x = self.model.NewIntVar(0, 10, 'x')
        self.model.Add(x >= 5)
        
        print("Solving...")
        try:
            status = self.solver.Solve(self.model)
            print(f"Status: {self.solver.StatusName(status)}")
        except Exception as e:
            print(f"CRASH: {e}")

print("--- Test 1: Basic Class ---")
sched = StrippedScheduler()
sched.solve()

print("\n--- Test 2: Importing scheduler_services ---")
try:
    from controllers.scheduler_services import CourseRepository
    print("Import Successful.")
except Exception as e:
    print(f"Import Failed: {e}")

print("\n--- Test 3: Importing curriculum_data ---")
try:
    sys.path.append(os.path.join(project_root, "database"))
    import curriculum_data
    print("Import Successful.")
except Exception as e:
    print(f"Import Failed: {e}")

print("\n--- Test 4: Running solve again after imports ---")
sched2 = StrippedScheduler()
sched2.solve()
