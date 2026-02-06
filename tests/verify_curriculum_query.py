import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.schedule_model import ScheduleModel

def verify_curriculum_query():
    test_db = "test_verification.db"
    
    # Needs seeded data from previous test (verify_pool_support.py)
    # If file exists, we assume data is there. If not, we might need to seed again.
    
    app = QApplication(sys.argv)
    model = ScheduleModel(db_path=test_db)
    
    # Ensure tables exist (auto-migration in init)
    
    print("Testing get_all_curriculum_details...")
    
    # 1. No Filter
    print("\n[Case 1] No Filter:")
    rows = model.get_all_curriculum_details()
    for r in rows:
        print(f"   -> {r}")
        
    if len(rows) > 0:
        print("   [PASS] Returned data.")
    else:
        print("   [WARN] No data returned. Did previous test run?")
        
    # 2. Filter by Dept
    print("\n[Case 2] Filter by Dept 101:")
    rows = model.get_all_curriculum_details(dept_id=101)
    for r in rows:
        print(f"   -> {r}")
        
    # 3. Filter by Year (Only Class courses should show)
    print("\n[Case 3] Filter by Year 1:")
    rows = model.get_all_curriculum_details(year=1)
    for r in rows:
         print(f"   -> {r}")

    print("\nDone.")

if __name__ == "__main__":
    verify_curriculum_query()
