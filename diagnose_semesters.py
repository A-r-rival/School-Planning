import sys
import os
import sqlite3

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from models.schedule_model import ScheduleModel

def diagnose_missing_semesters():
    db_path = os.path.join(current_dir, "database", "okul_veritabani.db")
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    model = ScheduleModel(db_path)
    model.initialize_connection()
    
    lookup = model.semester_lookup
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT ders_adi FROM Dersler")
    all_courses = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    missing = []
    for course_name in all_courses:
        res = lookup.get(course_name)
        if not res:
            base_name = course_name.split(' (')[0]
            res = lookup.get(base_name)
        if not res:
            missing.append(course_name)
            
    with open("results.txt", "w", encoding="utf-8") as f:
        f.write(f"Lookup count: {len(lookup)}\n")
        f.write(f"Missing count: {len(missing)} / {len(all_courses)}\n\n")
        f.write("Samples of missing courses:\n")
        for m in sorted(missing)[:50]:
            f.write(f" - {m}\n")
            
        f.write("\nChecking case-insensitivity...\n")
        lower_lookup = {k.lower(): v for k, v in lookup.items()}
        found_via_lower = [m for m in missing if m.lower() in lower_lookup]
        f.write(f"Found {len(found_via_lower)} matches via case-insensitive search.\n")
        if found_via_lower:
            for m in found_via_lower[:10]:
                f.write(f"   -> {m} matches {m.lower()} in lookup\n")

    print(f"Done. Missing: {len(missing)} / {len(all_courses)}")

if __name__ == "__main__":
    diagnose_missing_semesters()
