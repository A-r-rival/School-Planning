import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler

def test_generate_schedule():
    model = ScheduleModel()
    scheduler = ORToolsScheduler(model)
    
    print("Initializing schedule generation for Spring (Bahar)...")
    
    try:
        # Pass a timeout to prevent it from hanging if it's too complex
        # Note: We're calling generate_schedule directly!
        success = scheduler.generate_schedule(semester_filter="Bahar")
        print(f"Schedule Generation Result: {success}")
    except Exception as e:
        import traceback
        print(f"CRASH during generate_schedule: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_generate_schedule()
