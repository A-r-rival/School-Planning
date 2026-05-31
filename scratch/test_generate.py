"""
Test using the actual generate_schedule flow.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler

print("Loading model...", flush=True)
model = ScheduleModel()
scheduler = ORToolsScheduler(model)

print("Running generate_schedule('Güz')...", flush=True)
print("(This uses the real 2-phase pipeline with 80s Phase1 + 150s Phase2)", flush=True)
print("Waiting for result...", flush=True)

try:
    result = scheduler.generate_schedule(semester_filter="Güz")
    if result:
        print("\n✅ SUCCESS: Schedule generated!", flush=True)
        # Check how many items were saved
        import sqlite3
        conn = sqlite3.connect('database/okul_veritabani.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM Ders_Programi")
        count = c.fetchone()[0]
        conn.close()
        print(f"   Saved {count} schedule entries to DB.", flush=True)
    else:
        print("\n❌ FAILED: generate_schedule returned False", flush=True)
except Exception as e:
    import traceback
    print(f"\nERROR: {e}", flush=True)
    traceback.print_exc()
