import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler

def check_capacities():
    model = ScheduleModel("database/okul_veritabani.db")
    scheduler = ORToolsScheduler(model)
    scheduler.load_data("Bahar")
    
    room_caps = [r[3] if len(r) > 3 else 0 for r in scheduler.rooms]
    course_caps = [c.get('student_count', 0) for c in scheduler.courses]
    
    print(f"Room capacities: Min {min(room_caps)} - Max {max(room_caps)} (Avg {sum(room_caps)/len(room_caps):.1f})")
    print(f"Course capacities: Min {min(course_caps)} - Max {max(course_caps)} (Avg {sum(course_caps)/len(course_caps):.1f})")
    print("\nTop 10 largest courses:")
    sorted_c = sorted(scheduler.courses, key=lambda c: c.get('student_count', 0), reverse=True)
    for c in sorted_c[:10]:
        print(f"{c['name']} (Count: {c.get('student_count', 0)})")

if __name__ == "__main__":
    check_capacities()
