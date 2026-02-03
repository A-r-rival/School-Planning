from models.schedule_model import ScheduleModel
from controllers.scheduler_services import CourseRepository, CurriculumResolver
import collections

# 1. Initialize DB
model = ScheduleModel()

# 2. Instantiate Services
repo = CourseRepository(model)
resolver = CurriculumResolver(model)

# 3. Fetch Rows
print("--- FETCHING ROWS ---")
rows = repo.fetch_course_rows()

# 4. Check for expansion
print(f"Total rows fetched: {len(rows)}")

# Filter for courses that might have been expanded
# Known pool codes from previous logs: SDIa, SDIb, SDIc, SDIII, etc.
pool_ids = ['SDIa', 'SDIb', 'SDIc', 'SDIIa', 'SDIIb', 'SDIIc', 'SDIII', 'SDIV', 'USD001', 'USD002', 'USD000', 'SDP']

expanded_count = 0
for r in rows:
    if any(p in r.name or p in r.code for p in pool_ids):
        # If it's still a pool code in the name, it's NOT expanded (unless the actual course has that in name)
        # But if it's an actual course name, we should see it here
        pass

# Check resolve_context
print("\n--- RESOLVING CONTEXTS ---")
role_counts = collections.Counter()
for r in rows:
    ctx = resolver.resolve_context(r)
    role_counts[ctx.role.value] += 1
    if ctx.role.value == "ELECTIVE":
        if expanded_count < 10:
             print(f"ELECTIVE: {r.name} ({r.code}) -> Pool: {ctx.pool_code}")
             expanded_count += 1

print(f"\nRole Counts: {dict(role_counts)}")

model.conn.close()
