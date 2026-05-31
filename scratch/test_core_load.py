"""
Per-group CORE course load analysis — only mandatory courses count toward capacity.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schedule_model import ScheduleModel
from controllers.scheduler import ORToolsScheduler
from controllers.scheduler_services import CourseRole
from collections import defaultdict

model = ScheduleModel()
scheduler = ORToolsScheduler(model)

SEMESTER = "Güz"
scheduler.load_data(SEMESTER)

print(f"Courses after filter: {len(scheduler.courses)}")
cap = len(scheduler.time_slots)

# Only count CORE courses for capacity analysis
group_core_duration = defaultdict(int)
group_core_names = defaultdict(list)
group_elective_count = defaultdict(int)

for c in scheduler.courses:
    dur = c.get('duration', 0)
    contexts = c.get('program_contexts', [])
    
    # Check if this course is CORE for any group
    seen_groups = set()
    for gid in c.get('group_ids', []):
        if gid in seen_groups:
            continue
        seen_groups.add(gid)
        
        # Find contexts for this group
        is_core_for_group = False
        for ctx in contexts:
            if ctx.role == CourseRole.CORE:
                is_core_for_group = True
                break
        
        if is_core_for_group:
            group_core_duration[gid] += dur
            group_core_names[gid].append(c['name'][:30])
        else:
            group_elective_count[gid] += 1

sorted_groups = sorted(group_core_duration.items(), key=lambda x: x[1], reverse=True)

print(f"\nTop 15 groups by CORE course load:")
overloaded = []
for gid, load in sorted_groups[:15]:
    elec_count = group_elective_count.get(gid, 0)
    status = 'OVER!' if load > cap else 'OK'
    print(f"  {gid}: {load} slots core / {cap} cap [{status}] (+{elec_count} electives in pool)")
    if load > cap:
        overloaded.append((gid, load))
        print(f"    Core courses ({len(group_core_names[gid])}):")
        for cn in group_core_names[gid]:
            print(f"      - {cn}")

over_count = sum(1 for g, l in sorted_groups if l > cap)
print(f"\nOverloaded groups (core only): {over_count} / {len(group_core_duration)}")
print(f"\nCapacity ratio (mean): {sum(l for _,l in sorted_groups) / max(len(sorted_groups),1) / cap:.1%}")
