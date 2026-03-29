from models.schedule_model import ScheduleModel
from controllers.scheduler_services import CourseRepository, CurriculumResolver, CourseMerger, SchedulableCourseBuilder
model = ScheduleModel()
repo = CourseRepository(model)
rows = repo.fetch_course_rows()
resolver = CurriculumResolver()
merger = CourseMerger()
physical = merger.merge(rows, resolver)
builder = SchedulableCourseBuilder()
blocks = builder.build_blocks(physical)

lookup = model.semester_lookup

# Blocks without semester info
no_sem = [c for c in blocks if not (str(c.get('code','')).strip() in lookup)]
print(f"Blocks without semester info: {len(no_sem)}")
for c in no_sem[:10]:
    code = c.get("code", "?")
    name = c["name"][:60]
    ctype = c["type"]
    print(f"  code={code} name={name} type={ctype}")

# Blocks in both semesters
both = []
guz_only_list = []
bahar_only_list = []
for c in blocks:
    code = str(c.get('code','')).strip()
    if code in lookup:
        sem = lookup[code]
        if 'Bahar' in sem and 'Güz' in sem:
            both.append(c)
        elif sem == {'Güz'}:
            guz_only_list.append(c)
        elif sem == {'Bahar'}:
            bahar_only_list.append(c)

print(f"\nGuz-only: {len(guz_only_list)}")
print(f"Bahar-only: {len(bahar_only_list)}")
print(f"Both: {len(both)}")
print(f"Unknown: {len(no_sem)}")
print(f"After Guz filter should drop: {len(bahar_only_list)}")
