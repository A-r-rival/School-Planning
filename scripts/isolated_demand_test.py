import sqlite3
from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler
from controllers.scheduler_services import CourseRepository, CurriculumResolver, CourseMerger, SchedulableCourseBuilder

def isolated_test():
    model = ScheduleModel()
    scheduler = ORToolsScheduler(model)
    
    repo = CourseRepository(model)
    resolver = CurriculumResolver()
    merger = CourseMerger()
    builder = SchedulableCourseBuilder()
    
    raw_rows = repo.fetch_course_rows()
    physical_courses = merger.merge(raw_rows, resolver)
    all_courses = builder.build_blocks(physical_courses)
    
    # Keep only courses containing the target department context
    target_dept = "Enerji Bilimi ve Teknolojileri"
    target_year = 4
    
    isolated_courses = []
    
    for c in all_courses:
        for ctx in c.get('program_contexts', []):
            if ctx.department == target_dept and ctx.year == target_year:
                isolated_courses.append(c)
                break
                
    print(f"Isolated {len(isolated_courses)} courses for {target_dept}-{target_year}.")
    
    # Force scheduler to only use these
    scheduler.courses = isolated_courses
    
    from ortools.sat.python import cp_model
    scheduler.cp_model = cp_model.CpModel()
    scheduler.slots_per_day = 18
    scheduler.time_slots = [{'id': i} for i in range(90)]
    
    # We must fetch rooms
    model.c.execute("SELECT derslik_num, derslik_adi, derslik_tipi, kapasite FROM Derslikler WHERE silindi=0")
    scheduler.rooms = model.c.fetchall()
    scheduler.group_metadata = {}
    for r in raw_rows:
        if r.group_id and r.department:
            scheduler.group_metadata[r.group_id] = (r.department, r.class_year)
            
    # Add constraint structural dependencies
    import collections
    scheduler.teacher_day_spans = {}
    scheduler.teacher_unavail = collections.defaultdict(list)
    scheduler.group_slot_data = collections.defaultdict(lambda: {'cores': [], 'pools': collections.defaultdict(list)})
    scheduler.group_core_demand = collections.defaultdict(list)
    
    # Create variables
    scheduler.create_variables()
    print(f"Variables Created. Total Starts: {len(scheduler.starts)}")
    
    # Attempt a generic constraints pass without heavy lunch breaks
    scheduler.add_teacher_room_preferences()
    scheduler.add_student_group_conflicts()
    
    # Run
    scheduler.solver = cp_model.CpSolver()
    scheduler.solver.parameters.max_time_in_seconds = 30.0
    scheduler.solver.parameters.log_search_progress = True
    
    print("--- Running Isolated Solver ---")
    print("DEBUG: Before Solve() call", flush=True)
    import sys
    sys.stdout.flush()
    try:
        status = scheduler.solver.Solve(scheduler.cp_model)
        print(f"DEBUG: After Solve() call, status={status}", flush=True)
        from ortools.sat.python import cp_model
        if status == cp_model.OPTIMAL:
            print("Result: OPTIMAL")
        elif status == cp_model.FEASIBLE:
            print("Result: FEASIBLE")
        elif status == cp_model.INFEASIBLE:
            print("Result: INFEASIBLE")
        else:
            print("Result: UNKNOWN")
    except Exception as e:
        print(f"FAILED: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    isolated_test()
