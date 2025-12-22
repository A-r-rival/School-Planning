
import sys
import os
import sqlite3

# Add project root to path
sys.path.append(os.getcwd())

from controllers.scheduler import ORToolsScheduler
from models.schedule_model import ScheduleModel

def verify():
    print("Verifying Scheduler Logic...")
    model = ScheduleModel()
    
    # 1. Check Data Integrity
    print("\n[1] Checking Database for T/U/L columns...")
    try:
        model.c.execute("SELECT ders_adi, teori_saati, uygulama_saati FROM Dersler WHERE teori_saati > 0 AND uygulama_saati > 0 LIMIT 5")
        rows = model.c.fetchall()
        if not rows:
            print("WARNING: No courses found with both Theory and Practice hours > 0.")
        else:
            print(f"Found {len(rows)} sample courses with T & U:")
            for r in rows:
                print(f"  - {r[0]}: T={r[1]}, U={r[2]}")
    except Exception as e:
        print(f"ERROR: Column check failed: {e}")
        return

    # 2. Initialize Scheduler (loads data)
    print("\n[2] Initializing Scheduler (fetching courses)...", flush=True)
    import time
    time.sleep(1)
    scheduler = ORToolsScheduler(model)
    time.sleep(1)
    
    print("DEBUG: Calling load_data()...", flush=True)
    scheduler.load_data()
    
    print(f"DEBUG: Sc.rooms: {len(scheduler.rooms)}")
    
    # 3. Verify Internal State (T/U/L Splitting)
    print("\n[3] Verifying Course Splits in Memory...", flush=True)
    print(f"Total items in scheduler memory: {len(scheduler.courses)}", flush=True)
    if scheduler.courses:
        print(f"First item: {scheduler.courses[0]}")
        
    found_splits = False
    excluded_keywords = ["staj", "tez", "lisans bitirme çalışması", "işletmede mesleki eğitim", "mesleki uygulama"]
    found_excluded = []
    
    print("\n[4] Checking Exclusions...")
    for course in scheduler.courses:
        name_lower = course['name'].lower()
        for kw in excluded_keywords:
            if kw in name_lower:
                found_excluded.append(course['name'])
    
    if found_excluded:
        print(f"FAIL: Found excluded courses in scheduler: {found_excluded}")
    else:
        print("PASS: No excluded courses (Staj, Tez, etc.) found in scheduler.")

    print("\n[5] Verifying Multi-Part Splits...")
    for course in scheduler.courses:
        if course['type'] in ['Teori', 'Uygulama', 'Lab']:
            # Find a course with multiple parts
            name = course['name']
            parts = [c for c in scheduler.courses if c.get('parent_key') == course.get('parent_key')]
            
            if len(parts) > 1:
                print(f"PASS: Found multi-part course: {name}")
                for p in parts:
                    print(f"  - Type: {p['type']}, Duration: {p['duration']}, Room: {p['fixed_room']}")
                found_splits = True
                break
    
    if not found_splits:
        print("WARNING: No multi-part courses found in scheduler memory.")
        
    print("\nVerification Complete.")
    return

    # Original Solve Logic skipped
    # success = scheduler.solve()
                


if __name__ == "__main__":
    verify()
