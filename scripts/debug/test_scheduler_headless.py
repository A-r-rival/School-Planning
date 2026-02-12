
import sys
import os
import io

# Force UTF-8 for Windows console with line buffering
os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True, errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', line_buffering=True, errors='replace')

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
# scripts/debug -> scripts -> root
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.append(project_root)

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler

def run_test():
    print("Initializing Model...")
    model = ScheduleModel()
    
    print("Initializing Scheduler...")
    scheduler = ORToolsScheduler(model)
    
    print("Running SOLVE...")
    # NOTE: solve() internally calls load_data() and create_variables().
    # Do NOT call them manually beforehand — that creates stale variable
    # references from a different CpModel and causes infeasibility.
    success = scheduler.solve()
    
    if success:
        print("Scheduler finished successfully!")
        
        # Verify Room Preferences
        print("\n=== VERIFICATION: Room Preferences ===")
        
        model.c.execute("SELECT ogretmen_num, ad, soyad, room_request FROM Ogretmenler WHERE room_request IS NOT NULL")
        teachers_with_pref = model.c.fetchall()
        
        violation_count = 0
        check_count = 0
        
        for t in teachers_with_pref:
            t_id, name, surname, pref = t
            pref = pref.lower()
            
            # Get assigned courses
            model.c.execute("""
                SELECT dp.ders_adi, d.derslik_adi, d.floor
                FROM Ders_Programi dp
                JOIN Derslikler d ON dp.derslik_id = d.derslik_num
                WHERE dp.ogretmen_id = ?
            """, (t_id,))
            
            assignments = model.c.fetchall()
            
            if not assignments: continue
            
            print(f"\nChecking {name} {surname} (Pref: '{pref}'):")
            
            for asm in assignments:
                course, room, floor = asm
                room_lower = room.lower()
                floor = floor if floor is not None else 0
                
                check_count += 1
                is_violation = False
                reason = ""
                
                if "zemin" in pref or "giriş" in pref or "kat 0" in pref:
                    if floor != 0:
                        is_violation = True
                        reason = f"Expected Limit 0, got Floor {floor} ({room})"
                elif "kat 1" in pref:
                    if floor != 1:
                        is_violation = True
                        reason = f"Expected Floor 1, got Floor {floor} ({room})"
                elif "kat 2" in pref:
                    if floor != 2:
                        is_violation = True
                        reason = f"Expected Floor 2, got Floor {floor} ({room})"
                elif "lab" in pref:
                    if "lab" not in room_lower:
                        is_violation = True
                        reason = f"Expected Lab, got {room}"
                
                if is_violation:
                    print(f"  [FAIL] {course} -> {room} (Floor {floor}) - {reason}")
                    violation_count += 1
                else:
                    print(f"  [OK] {course} -> {room} (Floor {floor})")
                    
        print(f"\nVerification Complete. {check_count} assignments checked. {violation_count} violations found.")
            
    else:
        print("Scheduler failed to find a solution.")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        import traceback
        with open("error_log.txt", "a", encoding="utf-8") as f:
            f.write(f"\nCRITICAL ERROR IN MAIN: {e}\n")
            traceback.print_exc(file=f)
        print(f"CRITICAL ERROR: {e}")
