
import sys
print("Importing ORTools...")
try:
    from ortools.sat.python import cp_model
    print("ORTools imported.")
except ImportError:
    print("ORTools not found.")

print("Importing PyQt5...")
try:
    from PyQt5.QtCore import QObject
    print("PyQt5 imported.")
except ImportError:
    print("PyQt5 not found.")

def main():
    print("Creating CP Model...")
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()
    print("Solving...")
    solver.Solve(model)
    print("Solved.")

if __name__ == "__main__":
    main()
