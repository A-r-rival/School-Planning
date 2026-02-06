import sys
import os
from PyQt5.QtWidgets import QApplication

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.schedule_model import ScheduleModel

def verify_sections():
    test_db = "test_verification.db"
    
    app = QApplication(sys.argv)
    model = ScheduleModel(db_path=test_db)
    
    # 1. Filter: Havuz (99)
    print("\n[Case 1] Filter: Pool (99)")
    rows = model.get_all_curriculum_details(year=99)
    found_pool = False
    for r in rows:
        # Check sort key (Index 8)
        if r[8] == 99:
            found_pool = True
            print(f"   -> [Pool] {r[1]} (Key: {r[8]})")
        else:
            print(f"   -> [FAIL] Found non-pool: {r[1]} (Key: {r[8]})")
            
    if found_pool:
        print("   [PASS] Pool filter working.")
        
    # 2. Filter: Year 1
    print("\n[Case 2] Filter: Year 1")
    rows = model.get_all_curriculum_details(year=1)
    for r in rows:
        if r[8] == 1:
             print(f"   -> [Year 1] {r[1]} (Key: {r[8]})")
        elif r[8] == 99:
             print(f"   -> [WARN] Pool included in Year 1 filter?")
        else:
             print(f"   -> [FAIL] Found Year {r[8]} in Year 1 filter!")
             
    # 3. No Filter
    print("\n[Case 3] No Filter")
    rows = model.get_all_curriculum_details()
    last_key = -1
    sorted_ok = True
    for r in rows:
        if r[8] < last_key:
            sorted_ok = False
        last_key = r[8]
        print(f"   -> {r[1]} (Key: {r[8]})")
        
    if sorted_ok:
        print("   [PASS] Sorting correct.")
    else:
        print("   [FAIL] Sorting incorrect!")

    print("\nDone.")

if __name__ == "__main__":
    verify_sections()
