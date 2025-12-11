
import os
import sys

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir) # d:\D.P. Projesi
sys.path.append(project_root)

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler
from controllers.heuristic_scheduler import HeuristicScheduler
from ortools.sat.python import cp_model

def main():
    print("--- Running Scheduler ---")
    
    # Initialize Model
    model = ScheduleModel()
    
    # scheduler = ORToolsScheduler(model)
    scheduler = HeuristicScheduler(model) # Switch to Heuristic
    
    # Load Data
    print("Loading data...")
    scheduler.load_data()
    
    # Create Variables
    print("Creating variables...")
    scheduler.create_variables()
    
    # Add Constraints
    print("Adding constraints...")
    scheduler.add_hard_constraints()
    
    # Solve
    status = scheduler.solve()
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print("Schedule FOUND!")
        
        # Clear existing schedule?
        # model.c.execute("DELETE FROM Ders_Programi") # Optional, but good for retries
        # model.conn.commit()
        
        print("Saving schedule to database...")
        scheduler.extract_schedule()
        
        # Stats
        model.c.execute("SELECT COUNT(*) FROM Ders_Programi")
        count = model.c.fetchone()[0]
        print(f"Total scheduled slots: {count}")
        
    else:
        print("Could not find a feasible schedule.")
        
    model.close_connections()

if __name__ == "__main__":
    import traceback
    try:
        main()
    except Exception:
        traceback.print_exc()
