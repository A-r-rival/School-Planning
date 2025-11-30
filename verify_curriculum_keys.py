import sys
import os
sys.path.append(os.getcwd())
from scripts.curriculum_data import DEPARTMENTS_DATA

def verify_curriculum():
    dept = "Moleküler Biyoteknoloji"
    if dept in DEPARTMENTS_DATA:
        print(f"--- {dept} ---")
        curriculum = DEPARTMENTS_DATA[dept]["curriculum"]
        keys = sorted([int(k) for k in curriculum.keys()])
        print(f"Semesters found: {keys}")
        
        for k in keys:
            print(f"Semester {k}: {len(curriculum[str(k)])} courses")
            
        pools = DEPARTMENTS_DATA[dept]["pools"]
        pool_keys = sorted(pools.keys())
        print(f"Pools found: {pool_keys}")
        for pk in pool_keys:
            print(f"Pool {pk}: {len(pools[pk])} courses")
    else:
        print(f"{dept} not found in data.")

if __name__ == "__main__":
    verify_curriculum()
