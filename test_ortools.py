try:
    from ortools.sat.python import cp_model
    print("OR-Tools imported successfully")
    model = cp_model.CpModel()
    solver = cp_model.CpSolver()
    print("Solver created successfully")
except Exception as e:
    print(f"Error: {e}")
