import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from controllers.scheduler import ORToolsScheduler
from models.schedule_model import ScheduleModel

def check():
    db = ScheduleModel()
    scheduler = ORToolsScheduler(db)
    scheduler.load_data("Güz")
    
    print("\nFiltered Courses for Güz (Mekatronik 1. Sınıf):")
    
    g_id = '2024_105_1' # From previous output
    
    total = 0
    for c in scheduler.courses:
        if g_id in c.get('group_ids', []):
            dur = c.get('duration', 0)
            print(f"- {c['name']} (Inst {c['instance']}, Type {c['type']}): {dur} slots | Code: {c['code']}")
            total += dur
            
    print(f"Total Active Slots in Güz filter: {total}")

if __name__ == "__main__":
    check()
