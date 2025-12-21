
import sys
import os
import sqlite3

# Add current directory to path
current_dir = os.getcwd()
sys.path.insert(0, current_dir)

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler
from ortools.sat.python import cp_model
from PyQt5.QtCore import QCoreApplication

def check_database():
    app = QCoreApplication(sys.argv)
    print("Checking database content...")
    model = ScheduleModel()
    
    # Check Teachers
    teachers = model.get_all_teachers_with_ids()
    print(f"Teachers count: {len(teachers)}")
    if len(teachers) > 0:
        print(f"First 5 teachers: {teachers[:5]}")
    
    # Check Courses
    model.c.execute("SELECT COUNT(*) FROM Dersler")
    course_count = model.c.fetchone()[0]
    print(f"Courses count: {course_count}")
    
    # Check Faculties
    faculties = model.get_faculties()
    print(f"Faculties count: {len(faculties)}")

    return model

def inspect_data(model):
    print("\nInspecting existing data...")
    # Check Schedule
    model.c.execute("SELECT COUNT(*) FROM Ders_Programi")
    schedule_count = model.c.fetchone()[0]
    print(f"Schedule entries count: {schedule_count}")
    
    # Test specific queries used in Calendar View
    teachers = model.get_all_teachers_with_ids()
    if len(teachers) > 0:
        teacher_id = teachers[0][0]
        print(f"\nTesting get_schedule_by_teacher for teacher ID {teacher_id} ({teachers[0][1]})...")
        schedule = model.get_schedule_by_teacher(teacher_id)
        print(f"Schedule items: {len(schedule)}")
        if len(schedule) > 0:
            print(f"Sample item: {schedule[0]}")
        sys.stdout.flush()

def run_scheduler_test(model):
    print("\nTesting Scheduler Execution...")
    try:
        scheduler = ORToolsScheduler(model)
        # Try solving (dry run)
        print("Attempting to solve...")
        success = scheduler.solve() 
        print(f"Solve success: {success}")
        
    except Exception as e:
        print(f"Scheduler error: {e}")

if __name__ == "__main__":
    print("STARTING DEBUG SCRIPT")
    try:
        model = ScheduleModel() # Skip comprehensive check_database for now
        # inspect_data(model)
        run_scheduler_test(model) 
    except Exception as e:
        print(f"Global error: {e}")
        import traceback
        traceback.print_exc()
    print("ENDING DEBUG SCRIPT")

