# Add `group_size` to Scheduling Pipeline for Room Pre-filtering

## Goal
Add a student count (`ogrenci_sayisi`) to `Ogrenci_Donemleri`, flow it through the 
data pipeline into each course dict, and use it in [create_variables](file:///d:/Git_Projects/School-Planning/controllers/scheduler.py#219-398) to skip creating 
solver variables for rooms that are too small. This should significantly reduce the 
variable count (~1.3M → ~400K est.) and speed up the solver.

## Proposed Changes

---

### DB Layer

#### [NEW] [migration_010_add_group_size.py](file:///d:/Git_Projects/School-Planning/models/repositories/migrations/migration_010_add_group_size.py)
Add `ogrenci_sayisi INTEGER DEFAULT 0` column to `Ogrenci_Donemleri`.

#### [MODIFY] [migration.py](file:///d:/Git_Projects/School-Planning/models/repositories/migration.py)
Register `_010_add_group_size` in the ordered migrations list.

---

### UI Layer — Student Group Editor

#### [MODIFY] [schedule_model.py](file:///d:/Git_Projects/School-Planning/models/schedule_model.py)
- Update the `ogrenci_sinifi_ekle` method (INSERT into `Ogrenci_Donemleri`) to accept an optional `ogrenci_sayisi` parameter.
- Add a `sinif_ogrenci_sayisi_guncelle(donem_sinif_num, count)` method for edits.
- Update any SELECT queries that read student group info to also return `ogrenci_sayisi`.

> [!IMPORTANT]
> The UI currently has no field for entering student count. We'll add it wherever student groups are created/edited. Need to check which view/dialog handles this.

---

### Pipeline Layer

#### [MODIFY] [scheduler_services.py](file:///d:/Git_Projects/School-Planning/controllers/scheduler_services.py)

1. **[RawCourseRow](file:///d:/Git_Projects/School-Planning/controllers/scheduler_services.py#25-43)** — add `student_count: int = 0` field  
2. **[PhysicalCourse](file:///d:/Git_Projects/School-Planning/controllers/scheduler_services.py#55-80)** — add `student_count: int = 0` field; during merge, take the `max()` across all rows (a course taught to multiple groups → use the largest group's count, or sum — TBD with user)
3. **`CourseRepository.fetch_course_rows`** — add `od.ogrenci_sayisi` to the SELECT, populate `RawCourseRow.student_count`
4. **`SchedulableCourseBuilder.build_blocks`** — pass `student_count` into each block dict

---

### Scheduler Layer

#### [MODIFY] [scheduler.py](file:///d:/Git_Projects/School-Planning/controllers/scheduler.py)

In [create_variables](file:///d:/Git_Projects/School-Planning/controllers/scheduler.py#219-398), inside the room loop, after the lab/theory type check:
```python
# Capacity pre-filter
r_capacity = r[3] if len(r) > 3 else 0
course_size = course.get('student_count', 0)
if course_size > 0 and r_capacity > 0 and r_capacity < course_size:
    continue  # Room too small
```

---

## Open Questions

> [!NOTE]
> **For merged courses (multiple student groups):** If a course is taken by groups of size 30 and 50, should `student_count` be `max(30, 50) = 50` or `sum = 80`? 
> - `max` → the course is split across groups (most common case — parallel sections)
> - `sum` → all groups attend the same lecture together

Most likely `max` is correct, but confirm before implementing.

## Verification Plan
- Run [test_scheduler_crash.py](file:///d:/Git_Projects/School-Planning/test_scheduler_crash.py) and count variables before/after — expect ~40-60% reduction
- Run the scheduler and confirm UNKNOWN becomes FEASIBLE/OPTIMAL within the 400s timeout
