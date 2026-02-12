import sys
import os
# Add project root to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database"))
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from controllers.scheduler import ORToolsScheduler
from models.schedule_model import ScheduleModel
from controllers.scheduler_services import CourseRole
import io

# Force UTF-8 for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def debug_course_roles():
    print("Initializing Model...")
    model = ScheduleModel()
    scheduler = ORToolsScheduler(model)
    scheduler.load_data()
    
    print("\n--- Checking Specific Courses ---")
    target_courses = ["AIT", "ENG", "EBT"]
    
    # Find relevant courses
    found_courses = []
    for c in scheduler.courses:
        for t in target_courses:
            if t in c['code']:
                found_courses.append(c)
                
    print(f"Found {len(found_courses)} target courses.")
    
    for c in found_courses:
        print(f"\nCourse: [{c['code']}] {c['name']} (Instance {c['instance']})")
        print(f"  Group IDs: {c['group_ids']}")
        print(f"  Program Contexts:")
        for ctx in c['program_contexts']:
            print(f"    - Dept: {ctx.department}, Year: {ctx.year}, Role: {ctx.role}")
            
    print("\n--- Checking Group Metadata ---")
    # We need to see if the groups these courses belong to are actually mapped to the student's department/year
    # In the screenshot: "Enerji Bilimi ve Teknolojileri", Year 2.
    # We need to find the Group ID for this specific combo.
    
    target_dept = "Enerji Bilimi ve Teknolojileri"
    target_year = 2
    
    matching_groups = []
    print(f"\nScanning groups for {target_dept}, Year {target_year}...")
    for g_id, meta in scheduler.group_metadata.items():
        if isinstance(meta, tuple):
            dept, year = meta
            if dept == target_dept and year == target_year:
                print(f"  MATCH FOUND: Group ID '{g_id}' -> {meta}")
                matching_groups.append(g_id)
        elif meta == target_dept:
             pass
             
    if not matching_groups:
        print("  NO MATCHING GROUPS FOUND!")
        
    for g_id in matching_groups:
        print(f"\nChecking assignments for Group '{g_id}'")
        for c in found_courses:
            if g_id in c['group_ids']:
                role = scheduler.get_role_for_group(c, target_dept, target_year)
                print(f"  - [{c['code']}] is in this group. Role: {role}")
            else:
                print(f"  - [{c['code']}] is NOT in this group.")

if __name__ == "__main__":
    debug_course_roles()
