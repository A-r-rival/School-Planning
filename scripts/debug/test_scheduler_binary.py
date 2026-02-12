import sys
import os
import io

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

# Add project root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from controllers.scheduler import ORToolsScheduler
from models.schedule_model import ScheduleModel

class TestScheduler(ORToolsScheduler):
    def load_data(self):
        super().load_data()
        print(f"DEBUG: Slicing courses. Original: {len(self.courses)}")
        # Take first 10 core courses if possible
        # Check contexts to find core
        
        # Simple slice
        # Simple slice - disabled to test ALL courses
        # self.courses = self.courses[:200] 
        print(f"DEBUG: Sliced to: {len(self.courses)} courses.")

if __name__ == "__main__":
    print("Initializing DB Model...")
    db = ScheduleModel()
    
    print("Initializing Scheduler (Sliced)...")
    scheduler = TestScheduler(db)
    
    try:
        print("Running Sliced Solve...")
        success = scheduler.solve()
        print(f"Result: {success}")
    except Exception as e:
        print(f"CRASH: {e}")
