from ortools.sat.python import cp_model
import sys

def run():
    print("Creating Model...")
    model = cp_model.CpModel()
    
    print("Creating Vars...")
    vars = [model.NewBoolVar(f'v{i}') for i in range(10)]
    
    print("Adding Constraint...")
    model.Add(sum(vars) <= 1)
    
    print("Solving...")
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    status = solver.Solve(model)
    
    print(f"Status: {solver.StatusName(status)}")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"CRASH: {e}")
