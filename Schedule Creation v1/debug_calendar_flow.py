
import os
import sys

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # d:\D.P. Projesi
sys.path.append(project_root)

from models.schedule_model import ScheduleModel

def test_calendar_data():
    model = ScheduleModel()
    
    print("--- Testing Calendar Data Flow ---")
    
    # 1. Teachers
    teachers = model.get_all_teachers_with_ids()
    print(f"Found {len(teachers)} teachers.")
    
    if teachers:
        t_id, t_name = teachers[0]
        print(f"Checking schedule for teacher: {t_name} (ID: {t_id})")
        
        schedule = model.get_schedule_by_teacher(t_id)
        print(f"Schedule items: {len(schedule)}")
        for item in schedule:
            print(f" - {item}")
            
    # 2. Classrooms
    rooms = model.get_all_classrooms_with_ids()
    print(f"Found {len(rooms)} classrooms.")
    
    if rooms:
        r_id, r_name = rooms[0]
        print(f"Checking schedule for room: {r_name} (ID: {r_id})")
        
        schedule = model.get_schedule_by_classroom(r_id)
        print(f"Schedule items: {len(schedule)}")
        for item in schedule:
            print(f" - {item}")

    model.close_connections()

if __name__ == "__main__":
    test_calendar_data()
