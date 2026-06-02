# School-Planning — Code Audit Report
_Generated: 2026-06-01_

---

## 1. Duplicated Code

### 1a. Semester Detection — 5+ copies scattered everywhere

The pattern `"Güz" if radio_guz.isChecked() else ("Bahar" if radio_bahar.isChecked() else "Yaz")` is copy-pasted **5 times** across three files:

| File | Lines |
|------|-------|
| `schedule_controller.py` | 230–233, 312–314, 499–501, 670–673, 686–688 |
| `views/schedule_view.py` | 544, 563, 908 |
| `views/teacher_availability_view.py` | 591 |

**Fix:** Add a single helper on `ScheduleController` (or the view):
```python
def _get_current_semester(self) -> str:
    if self.view.radio_bahar.isChecked(): return "Bahar"
    if self.view.radio_yaz.isChecked():  return "Yaz"
    return "Güz"
```
Then replace all occurrences with `self._get_current_semester()`.

---

### 1b. Duplicate Progress-Dialog Comment

In `schedule_controller.py` lines **725–727** the same comment appears back-to-back:
```python
# Show Progress Dialog to inform user

# Show Progress Dialog to inform user
```
One should be deleted.

---

### 1c. Duplicate Stale Comment

In `schedule_controller.py` lines **397** and **751** both say:
```python
# Merging utilities moved to utils/schedule_merger.py
```
One is dead-weight. Keep only the first.

---

### 1d. `CourseRepository` — Split Personality (Two Cursor APIs)

`course_repo.py` has two groups of methods using *different* cursor attributes:

| Methods (lines 41–186) | Methods (lines 188–476) |
|---|---|
| Use `self._cursor` via `self._execute()` | Use `self.c`, `self.conn`, emit `self.error_occurred`, emit `self.course_added` — **none of which exist in `CourseRepository.__init__`** |

The lower half (`delete_curriculum_course`, `add_curriculum_course_as_template`, `get_curriculum_courses`, `get_courses_by_department`, `get_all_curriculum_details`) was moved from `ScheduleModel` but **never properly migrated**. They reference attributes (`self.c`, `self.conn`, `self.course_added`, `self.error_occurred`, `self.semester_lookup`) that belong to `ScheduleModel`, not `CourseRepository`. This code **will raise `AttributeError` at runtime** for those paths.

**Fix:** The `CourseRepository` constructor needs `conn` injected (the model already passes `self.c` but not `self.conn`). Or these methods need to be refactored to pass `conn` through the calling layer.

---

### 1e. `TeacherRepository` — Signal calls on a non-QObject

`teacher_repo.py` calls `self.error_occurred.emit(...)` in several methods (lines 244, 276, 295, 328, 355) — but `TeacherRepository` is a plain Python class, **not** a `QObject`. These calls will raise `AttributeError` at runtime whenever an error occurs in those methods.

Same bug as 1d. The signals should be raised as exceptions and caught by the caller (the model) which *does* have `error_occurred`.

---

### 1f. `get_active_schedule_version()` Called Redundantly in Every Query Method

Four methods inside `ScheduleModel` each independently resolve `versiyon_id`:
- `get_all_schedule_items` (line 324)
- `get_schedule_by_student_group` (line 607)
- `get_schedule_for_faculty_common` (line 706)
- `get_master_schedule_data` (line 1233)

Each does the same `if versiyon_id is None: versiyon_id = self.get_active_schedule_version()` boilerplate. Consider a cached `@property` or a single resolve at the call-site.

---

### 1g. Day-ordering CASE Duplicated in `teacher_repo.py`

The Turkish day-ordering `CASE` block (`Pazartesi=1 … Pazar=7`) appears **twice** in `teacher_repo.py`:
- `get_teacher_unavailability` (lines 141–149)
- `get_combined_availability` (lines 206–214)

**Fix:** Extract as a class-level constant string `_DAY_ORDER_SQL` and interpolate.

---

### 1h. `fakulte_ekle` / `bolum_ekle` Duplicated Between Model and Repositories

`ScheduleModel` still has raw implementations of `fakulte_ekle` (line 812) and `bolum_ekle` (line 851) with direct `self.c`/`self.conn` access, even though `FacultyDepartmentRepository` exists for this purpose. These are **dead duplicates** — the model's public API delegates to the repo (`add_faculty`, `add_department`), but these lower-level methods still sit in the model.

---

## 2. Obsolete / Dead Code

### 2a. Root-Level Temp & Fix Scripts (safe to delete)

These files serve no production purpose and aren't imported anywhere:
- `temp_test.py`, `temp_test2.py`, …, `temp_test6.py`
- `fix.py`, `fix2.py`, `fix3.py`
- `scratch.py`, `scratch_test2.py`, `scratch_test_filter.py`
- `check_courses.py`, `check_courses_y1.py`
- `output_debugging.txt`

---

### 2b. `export_schedule` / `import_schedule` Stub Methods

`schedule_controller.py` lines 255–274:
```python
def export_schedule(self, format_type: str = "text"):
    # TODO: Implement Excel export
    pass

def import_schedule(self, file_path: str):
    # TODO: Implement schedule import
    pass
```
These stubs are never called anywhere. An `ExcelExporter` service already exists in `services/excel_exporter.py`. Either wire them up or delete them.

---

### 2c. Commented-Out Span Code in Controller

`schedule_controller.py` lines 592–593:
```python
# span = self.model.get_teacher_span(teacher_id)
# self.availability_view.set_span(span)
```
Dead code. Remove.

---

### 2d. `semester_filter == "Yaz"` Always Skips in `get_all_schedule_items`

`schedule_model.py` lines 364–365:
```python
if semester_filter == "Yaz":
    continue
```
The Yaz branch unconditionally skips every row. There's no real Yaz semester logic. This should either be implemented or the check should be moved to the caller to avoid unnecessary per-row processing.

---

### 2e. `semester_filter == "Yaz"` Also a No-Op in `get_all_curriculum_details`

`course_repo.py` lines 415–418:
```python
if semester_filter == "Yaz":
    # We don't support Yaz yet in DB, just skip or show empty?
    # For now, let's just filtering logic handle it.
    pass
```
Dead branch — `pass` does nothing. Either filter or remove.

---

### 2f. `get_similar_course_groups` has a Pointless `get_base` Helper

`schedule_model.py` lines 1388–1389:
```python
def get_base(n):
    return n.strip()
```
This inner function just calls `.strip()`. It should be inlined.

---

### 2g. `QObject`-style Signal Pattern in `ScheduleApplication` (`main.py`)

`main.py` imports `pyqtSignal` but `ScheduleApplication` defines no signals. The import is unused:
```python
from PyQt5.QtCore import QObject, pyqtSignal
```
`pyqtSignal` can be removed from that import.

---

### 2h. `set_dark_theme` is Defined but Never Called

`main.py` defines `set_dark_theme(app)` (lines 65–127) but `main()` only calls `set_light_theme(app)`. The dark theme function is dead code unless there's a toggle. Either wire it to a menu action or delete it.

---

### 2i. SQL Comment Left in Query Code

`schedule_model.py` line 597:
```python
#SQL kuralı: GROUP BY kullanırken ...
```
A Turkish SQL tutorial comment inline in production code. Should be removed or moved to a docstring.

---

## 3. Optimization Opportunities

### 3a. `_build_semester_lookup` — Quadratic Inner-Loop setdefault Pattern

`schedule_model.py` lines 193–235: for each course, `setdefault` is called twice (once for global, once for dept-specific), and the pool expansion repeats the same pattern 4 more times. The repeated `if code not in self.semester_lookup` checks can be replaced with `setdefault` or a `defaultdict(set)`:

```python
# Before (repeated 3×):
if code not in self.semester_lookup:
    self.semester_lookup[code] = set()
self.semester_lookup[code].add(semester)

# After:
from collections import defaultdict
self.semester_lookup = defaultdict(set)
self.semester_lookup[code].add(semester)
```

---

### 3b. `get_classes_for_programs` — Two Separate DB Roundtrips Per Call

`schedule_model.py` lines 1164–1184 executes two separate queries (`query_regular` and `query_pool`) for the same set of `program_ids`. These can be merged into a single `UNION ALL` query, halving the roundtrips.

---

### 3c. `get_department_course_categories` — Two Separate Queries + Python Merge

`schedule_model.py` lines 1286–1313 also runs two queries and merges in Python. A single `UNION ALL` with a discriminator column would be cleaner and faster.

---

### 3d. `refresh_data` Calls `get_teachers` Twice

`schedule_controller.py`:
- `refresh_data()` (line 246): calls `self.model.get_teachers()` → `update_teacher_completer()`
- After `handle_add_course` (line 154): calls `get_teachers()` again immediately after `refresh_data()` was already triggered by the `course_added` signal (line 78)

This means adding a course fires `get_teachers()` **twice** in succession.

---

### 3e. `handle_remove_course_by_ids` Emits Signals Per-ID

`schedule_controller.py` lines 162–172: each `remove_course_by_id` triggers a `course_removed` signal which calls `refresh_data()`. Removing N courses triggers N full table refreshes. The signal should be suppressed during bulk deletions and fired once afterward.

---

### 3f. `room_repo.py` — Schema-Detection Try/Except on Every Query

`room_repo.py` uses `try/except` to check whether `floor` and `notlar` columns exist — for **every single query**:
```python
try:
    self.c.execute("SELECT ... floor, notlar FROM Derslikler ...")
except:
    self.c.execute("SELECT ... 0 as floor, '' as notlar FROM Derslikler ...")
```
This appears in at least 4 methods. The schema check should be done **once at init** and cached as a flag, not repeated per-call.

---

### 3g. `_patch_pool_sinif_duzeyi` Runs a Per-(dept, pool) COUNT Query in a Loop

`schedule_model.py` lines 138–145: the patch runs `N` individual `COUNT(*)` queries to check whether any rows need updating. This should be a single aggregated query.

---

### 3h. `auto_group_all_common_courses` — `MAX(grup_id)` Called Before the Transaction Block

`schedule_model.py` line 1500: `SELECT MAX(grup_id)` is called *inside* the `with self.conn:` block, but `current_grup_id` is also used to gate increments *across the loop iterations* without re-querying. This is correct as written, but the outer `SELECT MAX` at line 1500 queries before any inserts, creating a TOCTOU window if called concurrently (SQLite with `check_same_thread=False`).

---

## Summary Table

| Category | Count | Severity |
|---|---|---|
| Duplicate semester detection | 5+ copies | Medium |
| `CourseRepository` broken attrs (`self.c`, `self.conn`, signals) | ~6 methods | **High (runtime crash)** |
| `TeacherRepository` signal calls on non-QObject | ~5 methods | **High (runtime crash on error paths)** |
| Dead temp/fix/scratch files at root | ~12 files | Low |
| `export_schedule` / `import_schedule` stubs | 2 methods | Low |
| Unused `set_dark_theme` | 1 function | Low |
| Duplicate DB queries (two roundtrips → one UNION) | 2 methods | Medium |
| Per-query schema detection in `room_repo` | 4 methods | Medium |
| `refresh_data` + `get_teachers` double-call | 1 flow | Low |
| Bulk-delete N-signal-N-refresh | 1 flow | Medium |
