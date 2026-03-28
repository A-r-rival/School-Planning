import os
import sys

# Add the project root to the sys_path
current_dir = os.path.dirname('d:/Git_Projects/School-Planning/controllers/scheduler_services.py')
sys.path.insert(0, 'd:/Git_Projects/School-Planning')

from models.schedule_model import ScheduleModel
from controllers.scheduler_services import CourseRepository

def test_pools():
    model = ScheduleModel('d:/Git_Projects/School-Planning/database/okul_veritabani.db')
    repo = CourseRepository(model)
    pool_map = repo._build_pool_year_map()
    
    # Dump to a file or print
    target_dept = "Mekatronik Müh"
    print(f"Pool map for {target_dept}:")
    for key, val in pool_map.items():
        if key[0] == target_dept:
            print(f"{key}: {val}")
            
    # Let's also check if 'ZSD' is present
    print("\nLooking for 'ZSD' specifically across all depts:")
    for key, val in pool_map.items():
        if 'ZSD' in key[1]:
            print(f"{key}: {val}")

if __name__ == "__main__":
    test_pools()
