import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule_model import ScheduleModel

def debug_calendar_data():
    print("--- Calendar Data Debug ---")
    model = ScheduleModel()
    
    # 1. Check Faculties
    print("\n[1] Checking Faculties...")
    faculties = model.get_faculties()
    print(f"Total Faculties: {len(faculties)}")
    
    if not faculties:
        print("!! NO FACULTIES FOUND !!")
        return

    # 2. Find a Faculty with Departments
    target_faculty = None
    target_dept = None
    
    print("\n[2] searching for a faculty with departments...")
    for f_id, f_name in faculties:
        depts = model.get_departments_by_faculty(f_id)
        if depts:
            print(f"FOUND: Faculty '{f_name}' (ID: {f_id}) has {len(depts)} departments.")
            target_faculty = (f_id, f_name)
            target_dept = depts[0] # (id, name)
            break
        else:
            # excessive printing avoidance
            pass
            
    if not target_dept:
        print("!! NO DEPARTMENTS FOUND IN ANY FACULTY !!")
        # List a few faculties to check IDs
        print("Sample Faculties and their IDs:")
        for f in faculties[:5]:
             print(f"  - {f}")
        return

    print(f"Target Dept: {target_dept[1]} (ID: {target_dept[0]})")

    # 3. Check Student Schedule (Unpacking Crash Test)
    # Check years 1-4
    print(f"\n[3] Checking Schedule for Dept {target_dept[1]}, Years 1-4...")
    for year in range(1, 5):
        schedule = model.get_schedule_by_student_group(target_dept[0], year)
        print(f"  Year {year}: {len(schedule)} events found.")
        if schedule:
            first_item = schedule[0]
            print(f"  -> Sample Item ({len(first_item)} elements): {first_item}")
            if len(first_item) != 5:
                print(f"  !! MISMATCH DETECTED !! Expected 5, got {len(first_item)}")
            
            # If we found a schedule, no need to check other years for crash reproduction
            break

if __name__ == "__main__":
    debug_calendar_data()
