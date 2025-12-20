
import sys
import os

# Add current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import ORTools first to avoid conflict with PyQt5
try:
    from ortools.sat.python import cp_model
except ImportError:
    pass

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler

def main():
    print("Initializing Model...")
    try:
        model = ScheduleModel("okul_veritabani.db")
    except Exception as e:
        print(f"Failed to init model: {e}")
        return

    print("Initializing Scheduler...")
    try:
        scheduler = ORToolsScheduler(model)
    except Exception as e:
        print(f"Failed to init scheduler: {e}")
        return

    print("Calling solve()...")
    try:
        status = scheduler.solve()
        print(f"Solve returned status: {status}")
    except Exception as e:
        print(f"Crash during solve: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
