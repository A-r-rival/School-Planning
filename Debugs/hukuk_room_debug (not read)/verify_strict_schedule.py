
import sys
import os
import time

# Add current directory to path
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

from ortools.sat.python import cp_model
from controllers.scheduler import ORToolsScheduler
from models.schedule_model import ScheduleModel

def test_strict_mode():
    print("Testing Strict Scheduling Mode (All Constraints)...")
    
    try:
        model = ScheduleModel()
        scheduler = ORToolsScheduler(model)
        
        # Load Data
        scheduler.load_data()
        
        # Add ALL Constraints explicitly
        print("Adding Hard Constraints (Teachers + Fixed Rooms)...")
        scheduler.cp_model = cp_model.CpModel()
        scheduler.create_variables()
        scheduler.add_hard_constraints(include_teacher_unavailability=True)
        
        # Configure Solver
        scheduler.solver.parameters.log_search_progress = True
        scheduler.solver.parameters.log_to_stdout = True
        scheduler.solver.parameters.max_time_in_seconds = 30.0 
        
        print("Solving...")
        start_time = time.time()
        status = scheduler.solver.Solve(scheduler.cp_model)
        duration = time.time() - start_time
        
        print(f"\nSolver finished in {duration:.2f} seconds.")
        print(f"Status: {scheduler.solver.StatusName(status)}")
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print("SUCCESS: Schedule generated with STRICT constraints!")
            return True
        else:
            print("FAIL: Still INFEASIBLE with strict constraints.")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    try:
        test_strict_mode()
    except Exception as e:
        print(f"CRITICAL SCRIPT FAILURE: {e}")
        import traceback
        traceback.print_exc()
