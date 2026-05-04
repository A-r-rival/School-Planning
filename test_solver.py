import sys
sys.path.append("d:/Git_Projects/School-Planning")
from utils.layout_solver import solve_layout
from database.db_manager import DatabaseManager
from services.scheduler_services import SchedulerServices
import json

db = DatabaseManager("d:/Git_Projects/School-Planning/database/school_planning.db")
services = SchedulerServices(db)
res = services.get_weekly_schedule_for_entity("student_group", 1) # Assuming SG 1
events = []
for d, evs in res.items():
    if d == "Çarşamba": # The problematic day
        events = evs
        break

slot_occ = {i: [] for i in range(18)}
for e in events:
    for i in range(int(e['start_slot']), int(e['end_slot'])):
        if 0 <= i < 18:
            slot_occ[i].append(e)

layout = solve_layout(events, slot_occ)
if layout is None:
    print("SOLVER FAILED (INFEASIBLE)")
else:
    print("SOLVER SUCCESS")
