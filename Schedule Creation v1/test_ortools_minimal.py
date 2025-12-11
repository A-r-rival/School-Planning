
from ortools.sat.python import cp_model

def test_minimal():
    print("Creating model...")
    model = cp_model.CpModel()
    x = model.NewBoolVar('x')
    y = model.NewBoolVar('y')
    model.Add(x != y)
    
    print("Creating solver...")
    solver = cp_model.CpSolver()
    
    print("Solving...")
    status = solver.Solve(model)
    print(f"Status: {solver.StatusName(status)}")
    
    if status == cp_model.OPTIMAL:
        print(f"x={solver.Value(x)}, y={solver.Value(y)}")

if __name__ == "__main__":
    try:
        test_minimal()
    except Exception as e:
        print(f"Crash: {e}")
