import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler

def run_solver():
    try:
        print("Initializing ScheduleModel...")
        model = ScheduleModel()
        
        print("Initializing ORToolsScheduler...")
        scheduler = ORToolsScheduler(model)
        
        print("Running generate_schedule()...")
        success = scheduler.generate_schedule()
        
        print(f"Schedule generation finished. Success: {success}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    run_solver()
