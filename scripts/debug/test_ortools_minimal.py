
from ortools.sat.python import cp_model
import sys

print(f"Python Version: {sys.version}")

try:
    import ortools
    print(f"OR-Tools Version: {ortools.__version__}")
except Exception as e:
    print(f"Error importing ortools: {e}")

print("Initializing CP Model...")
model = cp_model.CpModel()
x = model.NewIntVar(0, 10, "x")
model.Add(x >= 5)

print("Initializing Solver...")
solver = cp_model.CpSolver()
solver.parameters.log_search_progress = True

print("Solving...")
status = solver.Solve(model)

print(f"Status: {solver.StatusName(status)}")
print(f"Value of x: {solver.Value(x)}")
