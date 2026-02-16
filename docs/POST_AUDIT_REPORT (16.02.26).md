# Post-Audit Report — Code Cleanup (16.02.2026)

This report documents the code audit and cleanup performed on 16.02.2026.
It supersedes the old `OBSOLETE_FUNCTIONS (08.02.26).md` file (now deleted).

---

## Summary

| Metric | Value |
|--------|-------|
| Files modified | 4 (`schedule_controller.py`, `schedule_model.py`, `schedule_view.py`, `schedule_merger.py`) |
| Files deleted | 3 (`scheduler_ortools.py`, `fix_room_saturation.py`, `OBSOLETE_FUNCTIONS (08.02.26).md`) |
| Files archived | 2 (`heuristic_scheduler.py`, `run_scheduler.py` → `scripts/archive/`) |
| Lines removed | ~500 |
| Functions removed | 15 |
| Signals removed | 1 |
| Imports cleaned | 3 |

---

## What Was Removed

### Controller (`controllers/schedule_controller.py`)
- `handle_remove_course()` — legacy string-based removal, superseded by `handle_remove_course_by_ids()`
- `validate_schedule()` — empty stub, never wired to UI
- `get_statistics()` — broken (called non-existent `model.get_all_courses()`)
- `clear_inputs()` call — called a no-op stub on the view
- Signal connection: `course_remove_requested → handle_remove_course` (signal was never emitted)
- Dead code block: ~30 lines of stale solver-return-type reasoning in `_run_scheduler`
- Unused imports: `merge_course_strings`, redundant top-level `MasterScheduleView`

### Model (`models/schedule_model.py`)
- `remove_course(str)` — deprecated regex-based string parser
- `get_all_courses_as_string()` — legacy formatter, only caller was dead code
- `_validate_course_data()` — unused, validation moved to `CourseInput`/`ScheduleService`
- `_has_slot_conflict()` — deprecated wrapper, never called
- `_check_time_conflict()` — deprecated wrapper, never called
- 3 duplicate definitions (Python shadowed first copies):
  - `get_all_classrooms_with_ids()` (simpler version without floor/natural sort)
  - `get_faculties()` (identical duplicate)
  - `get_departments_by_faculty()` (identical duplicate)
- FROZEN comment block (freeze no longer in effect after audit)

### View (`views/schedule_view.py`)
- `course_remove_requested` signal — defined but never emitted
- `clear_inputs()` — no-op stub (`pass`)

### Deleted Files
- `controllers/scheduler_ortools.py` — 76-line debug stub (see explanation below)
- `utils/fix_room_saturation.py` — one-off room optimization script, never imported
- `OBSOLETE_FUNCTIONS (08.02.26).md` — superseded by this report

### Archived Files (moved to `scripts/archive/`)
- `controllers/heuristic_scheduler.py` — early greedy scheduler, superseded by OR-Tools (see explanation below)
- `scripts/run_scheduler.py` — CLI runner for the scheduler, stale (called `solve()` instead of `generate_schedule()`)

### Utilities (`utils/schedule_merger.py`)
- `merge_course_strings()` — 95-line function operating on legacy string-formatted courses. No importers remained after `merge_course_strings` import was cleaned from controller. The other two functions in the file (`merge_consecutive_blocks`, `merge_schedule_items_dicts`) are actively used.
- `import re` — only used by the deleted function

### Verified Active (No Action Needed)
- `ScheduleFormatter` in `models/formatters/` — actively called in `schedule_model.py:add_course()` to format `ScheduledCourse` entities for the `course_added` signal. Correctly scoped within the model layer.

---

## What Was Preserved (Marked as FUTURE)

These stub methods were kept and marked with `FUTURE:` docstrings and `# TODO` comments:
- `export_schedule()` — planned for eventual Excel export
- `import_schedule()` — planned for eventual schedule import from file

They will show up as a separate group in future audits.

---

## Explanations

### Why was `scheduler_ortools.py` a debug stub?

This 76-line file was created as a **minimal reproduction** to verify that the OR-Tools solver could be initialized and run without crashing. Its purpose was to isolate whether solver failures were caused by the data/constraints or by the OR-Tools setup itself.

Evidence of its debug nature:
- All data-loading methods were empty (`pass`)
- `create_variables()` created a single dummy boolean variable and added a trivial constraint (`x == 1`)
- `solve()` printed `"MINIMAL SOLVE (RECREATED FILE)"` — literally naming itself as a recreated debug file
- All imports needed for real scheduling (curriculum data, course services) were commented out
- The real scheduler lives in `controllers/scheduler.py` (~1245 lines) and is the one imported by the controller

It was never imported anywhere, and had no downstream consumers.

### Why was `heuristic_scheduler.py` archived?

The heuristic scheduler was an early, simpler approach using a greedy algorithm: iterate through courses, try to assign each to the first available (room, timeslot) pair that doesn't conflict. It was superseded by the OR-Tools constraint programming scheduler, which can:
- Guarantee optimal or feasible solutions
- Handle complex constraints (teacher availability, room capacity, compactness)
- Backtrack intelligently instead of greedily failing

It was stale: it ignored `preferred_day_span`, didn't handle semester filtering or pool courses, and its only caller (`run_scheduler.py`) used the old `solve()` API. Archived to `scripts/archive/` for historical reference.

### Why was `clear_inputs()` a no-op?

In the original design, the view had inline input fields (text boxes, dropdowns) directly embedded in the main window. After a course was added, `clear_inputs()` would reset those fields.

The UI was later refactored to use a **dialog-based approach** (`AddCourseDialog`). Dialogs are ephemeral — they're created, used, and destroyed each time. There are no persistent input fields to clear. The method was kept as a `pass` stub to avoid breaking the controller's call to `self.view.clear_inputs()`, but both the call and the stub were dead code.

---

## Recommendations for Future Audits

1. **Search for duplicate method definitions** in large files — Python silently uses the last definition
2. **Check signal wiring**: look for `pyqtSignal` definitions that are `connect()`-ed but never `.emit()`-ed
3. **FUTURE-marked methods** (`export_schedule`, `import_schedule`) should be implemented or removed
