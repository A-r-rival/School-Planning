
from ortools.sat.python import cp_model

def test_medium():
    print("Creating model...")
    model = cp_model.CpModel()
    
    num_courses = 50
    num_rooms = 20
    num_slots = 40
    
    room_vars = {}
    time_vars = {}
    
    print("Creating variables...")
    count = 0
    for c in range(num_courses):
        current_course_rooms = []
        for r in range(num_rooms):
            rv = model.NewBoolVar(f'c{c}_r{r}')
            room_vars[(c, r)] = rv
            current_course_rooms.append(rv)
            
            for s in range(num_slots):
                tv = model.NewBoolVar(f'c{c}_r{r}_s{s}')
                time_vars[(c, r, s)] = tv
                count += 1
        
        # Add constraint like in scheduler
        model.Add(sum(current_course_rooms) == 1)
        
    print(f"Created {count} variables.")
    print("Solving...")
    solver = cp_model.CpSolver()
    solver.parameters.log_search_progress = True
    status = solver.Solve(model)
    print(f"Status: {solver.StatusName(status)}")

if __name__ == "__main__":
    try:
        test_medium()
    except Exception as e:
        print(f"Crash: {e}")
