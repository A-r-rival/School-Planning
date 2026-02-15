
import sys
import os
import json

# Add database dir to path
sys.path.append(os.path.join(os.getcwd(), "database"))

try:
    import curriculum_data
except ImportError:
    sys.exit(1)

def inspect():
    energy_key = None
    for key in curriculum_data.DEPARTMENTS_DATA.keys():
        if "Enerji" in key:
            energy_key = key
            break
            
    if not energy_key:
        print("Energy Department not found.")
        return

    dept_data = curriculum_data.DEPARTMENTS_DATA[energy_key]
    curriculum = dept_data.get("curriculum", {})
    
    # Check Semester 5 and 6
    for sem in ["5", "6"]:
        print(f"\n--- Semester {sem} Courses ---")
        courses = curriculum.get(sem, [])
        for c in courses:
            code = c[0]
            name = c[1]
            akts = c[2]
            if "ZSD" in code or "SD" in code or "Seçmeli" in name:
                print(f"FOUND: {code} - {name} ({akts} AKTS)")

if __name__ == "__main__":
    inspect()
