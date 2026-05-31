# Walkthrough: Bug Fixes & Scheduling Optimizations (31.05.2026)

This document summarizes the fixes and feature additions implemented to resolve critical rendering bugs, optimize the OR-Tools scheduling logic, and improve the user interface for comparing schedules.

## 1. Calendar View Bug Fixes & Stability
**File:** `views/calendar_view.py`

Several issues were preventing the calendar from rendering correctly, particularly for mandatory courses and during rapid UI updates.

*   **Scoping Bug Fixed (`NameError`):** In `_filter_slots`, the `pools` variable was only being defined if a course was an elective. When processing mandatory courses, the code crashed trying to read `pools`. We fixed this by correctly defaulting `pools` and restructuring the fallback logic.
*   **Metadata Retention:** In `display_schedule`, the `last_metadata` attribute was being overwritten with an empty dictionary before checking if the new data had metadata. We implemented a safeguard using `getattr` to preserve the previous metadata when re-rendering.
*   **PyQt5 Compatibility:** Replaced the context manager `QSignalBlocker` (which is not available in older PyQt5 bindings) with robust `blockSignals(True)` and `blockSignals(False)` calls to prevent recursive signal firing during programmatic dropdown updates.

## 2. OR-Tools Scheduler Optimizations
**File:** `controllers/scheduler.py`

The core scheduling algorithm was making mathematically optimal but practically undesirable decisions regarding multi-part courses and parallel electives.

*   **Day Separation Penalty Increased:** 
    *   *Problem:* Multi-part courses like "Fabrika Yönetimi" (Teori, Lab, Uygulama) were being scheduled on the exact same day because the penalty for doing so (`-5` in Phase 2) was heavily outweighed by the reward of scheduling them, or simply ignored due to its low baseline weight (`1` in Phase 1).
    *   *Fix:* We multiplied the boolean `conflict` penalty by `50` in `add_soft_constraints_consecutive`. The solver is now heavily disincentivized from placing parts of the same course on the same day unless absolutely forced by hard constraints.
*   **Parallel Elective Spreading:**
    *   *Problem:* Up to 5 different elective lab sessions (e.g., MEC033, MAB309) were being clustered into the exact same 1-hour slot on Thursday. The solver did this because it mathematically freed up the rest of the week for core courses, but it resulted in a crammed schedule.
    *   *Fix:* Added a new soft penalty (`elective_overlap_penalties`) in `add_student_group_conflicts`. The solver now incurs a penalty equal to `(number of overlapping electives - 1)`. This soft constraint encourages the solver to distribute elective courses more evenly across the week.

## 3. UI Enhancements: Schedule Compare View
**File:** `views/schedule_compare_view.py` & `views/schedule_view.py`

*   **Quick Filter Copy Buttons:** 
    *   Added two quick-action buttons (**➡️** and **⬅️**) to the "Karşılaştır ve Düzenle" (Compare & Edit) top bar.
    *   These buttons allow users to instantly copy their complex filter selections (View Type, Teacher/Room/Faculty, Department, and Year) from the left calendar to the right calendar (or vice versa) without having to manually select dropdowns multiple times.

---

> [!NOTE]  
> All changes have been tested locally and ensure both backward compatibility with existing saved schedules and a much more realistic distribution of classes in newly generated schedules.

## 4. Manual Schedule Editing Workflow
**Files:** `views/manual_edit_dialog.py`, `views/schedule_compare_view.py`, `models/repositories/schedule_repo.py`, `services/calendar_schedule_builder.py`

Implemented a complete end-to-end workflow to manually edit the time and room for any scheduled block directly from the comparison view.

*   **Database Pipeline Upgrade:** `program_id` is now fetched across all schedule querying routines and propagated down through the UI tuple rendering sequence (`CalendarScheduleBuilder`).
*   **UI Integration (`DayCanvas`):** The calendar's polygon rendering engine was enhanced to detect mouse clicks precisely on non-rectangular SVG-style blocks, emitting the relevant course data payload (including `program_id`).
*   **Manual Edit Dialog:** Added a dynamic UI component allowing the user to select a new Day, Start Time, End Time, and Room (Classroom) for a specific course block.
*   **Conflict Validation:** The backend now intercepts the move request and tests it against `ScheduleRepository.has_conflict`. The move is blocked and a warning is issued if the teacher or the requested room is already occupied during the target slot (excluding its own current footprint).
