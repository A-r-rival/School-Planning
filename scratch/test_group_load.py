"""
Per-group course load analysis after semester filter.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler
from collections import defaultdict

model = ScheduleModel()
scheduler = ORToolsScheduler(model)

SEMESTER = "Güz"
scheduler.load_data(SEMESTER)

print(f"Courses after filter: {len(scheduler.courses)}")
print(f"Slots per week (capacity per group): {len(scheduler.time_slots)}")

# Count UNIQUE courses per group (not sum of group_ids occurrences)
# Each schedulable block has group_ids - count each block once per group
group_duration = defaultdict(int)
group_courses = defaultdict(list)

for c in scheduler.courses:
    dur = c.get('duration', 0)
    seen_groups = set()  # Avoid double-counting for the same course
    for gid in c.get('group_ids', []):
        if gid not in seen_groups:
            group_duration[gid] += dur
            group_courses[gid].append(c['name'][:30])
            seen_groups.add(gid)

# Sort by load descending
sorted_groups = sorted(group_duration.items(), key=lambda x: x[1], reverse=True)

print(f"\nTop 10 most loaded groups:")
cap = len(scheduler.time_slots)
for gid, load in sorted_groups[:10]:
    status = 'OVER!' if load > cap else 'OK'
    print(f"  {gid}: {load} slots / {cap} cap [{status}]")
    if load > cap:
        print(f"    Courses ({len(group_courses[gid])}):")
        for cn in group_courses[gid][:5]:
            print(f"      - {cn}")

overloaded = [(g, l) for g, l in sorted_groups if l > cap]
print(f"\nOverloaded groups: {len(overloaded)} / {len(group_duration)}")
