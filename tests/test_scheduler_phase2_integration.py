import sys
import os
import logging
from collections import defaultdict

# Add project root to path
PROJECT_ROOT = r"d:\Git_Projects\School-Planning"
sys.path.append(PROJECT_ROOT)

from controllers.scheduler import ORToolsScheduler
from PyQt5.QtWidgets import QApplication
from models.schedule_model import ScheduleModel

def verify_scheduler():
    print("=== Phase 2 Integration Verification ===")
    
    # Init Qt App (required for Model signals)
    app = QApplication(sys.argv)
    
    # Init Model
    db_path = os.path.join(PROJECT_ROOT, "okul_veritabani.db")
    if not os.path.exists(db_path):
        print(f"ERROR: Database not found at {db_path}")
        return
        
    print(f"Loading Model from: {db_path}")
    sys.stdout.flush()
    try:
        model = ScheduleModel(db_path)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Model Init Failed: {e}")
        return
    sys.stdout.flush()
    
    # Init Scheduler
    print("Initializing Scheduler...")
    sys.stdout.flush()
    try:
        scheduler = ORToolsScheduler(model)
        print("Scheduler initialized.")
    except Exception as e:
        print(f"Scheduler Init Failed: {e}")
        return
    sys.stdout.flush()
    
    # Run Solve
    print("Running solve()...")
    sys.stdout.flush()
    
    try:
        success = scheduler.solve()
    except Exception as e:
        print(f"\nCRITICAL EXCEPTION during solve: {e}")
        import traceback
        traceback.print_exc()
        return

    print(f"\nSolve Return Value: {success}")
    
    if success:
        print("SUCCESS! Scheduler completed execution.")
        
        # Validation checks
        constraints_count = len(scheduler.cp_model.Proto().constraints)
        print(f"Constraints Generated: {constraints_count}")
        
        vars_count = len(scheduler.cp_model.Proto().variables)
        print(f"Variables Created: {vars_count}")
        
        if constraints_count == 0:
            print("WARNING: 0 Constraints! Something is wrong.")
            
        if vars_count == 0:
            print("WARNING: 0 Variables! Something is wrong.")
            
    else:
        print("FAILURE: Scheduler returned False.")

if __name__ == "__main__":
    verify_scheduler()
