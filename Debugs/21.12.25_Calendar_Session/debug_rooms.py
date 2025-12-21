import sys
import os
import sqlite3

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule_model import ScheduleModel

def debug_room_assignments():
    print("--- Room Assignment Debug ---")
    model = ScheduleModel()
    
    # Check if Dersler has any room assignments
    query = "SELECT ders_adi, teori_odasi, lab_odasi FROM Dersler WHERE teori_odasi IS NOT NULL OR lab_odasi IS NOT NULL LIMIT 10"
    model.c.execute(query)
    rows = model.c.fetchall()
    
    print("\n[Dersler with Assigned Rooms (Limit 10)]")
    if rows:
        for r in rows:
            print(f"  - {r}")
    else:
        print("  !! NO COURSES HAVE ASSIGNED ROOMS.")
        
    # Check if we have any classrooms
    model.c.execute("SELECT COUNT(*) FROM Derslikler")
    count_rooms = model.c.fetchone()[0]
    print(f"\nTotal Classrooms/Rooms: {count_rooms}")
    
    # Check if schedule exists
    model.c.execute("SELECT COUNT(*) FROM Ders_Programi")
    count_schedule = model.c.fetchone()[0]
    print(f"Total Schedule Entries: {count_schedule}")

if __name__ == "__main__":
    debug_room_assignments()
