
from ortools.sat.python import cp_model
import sys

def main():
    print("Creating model...")
    model = cp_model.CpModel()
    print("Creating solver...")
    solver = cp_model.CpSolver()
    print("Solving empty model...")
    solver.parameters.log_search_progress = True
    solver.parameters.log_to_stdout = True
    try:
        status = solver.Solve(model)
        print(f"Status: {solver.StatusName(status)}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
