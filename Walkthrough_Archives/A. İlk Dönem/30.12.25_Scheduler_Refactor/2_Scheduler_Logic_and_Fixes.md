# Scheduler Refactoring Phase 2: Logic, Stability & Fixes

## 1. Overview
This document covers the second half of the massive "Scheduler Refactoring" initiative. After extracting components in Phase 1, we focused on integrating them, ensuring stability, and fixing critical logic bugs that were causing infeasibility and display errors.

## 2. Key Architecture Changes

### A. Two-Phase Solving with Stable Keys
We moved from a fragile index-based approach to a robust **Stable Key** system for preserving assignments between phases.

- **Problem:** Phase 1 (Cores) assignments were saved as `(index, room_id, slot_id)`. If Phase 2 sorting changed the order of `self.courses`, the indices would point to the wrong courses, causing chaos.
- **Solution:** We now save assignments using `(CourseName, Instance, CourseType)`.
- **Logic:**
  1. **Phase 1 (Cores Only):** Solving for core courses.
  2. **Extraction:** Assignments extracted as `stable_assignments = list((c.name, c.instance, c.type), r_id, s_id)`.
  3. **Phase 2 (Electives):** Creating variables for ALL courses.
  4. **Re-Application:** We map the stable keys back to the *new* indices of Phase 2 and strictly enforce: `model.Add(start_var == 1)`.

### B. Soft Constraints for Feasibility
We replaced "hard infeasibility" with "soft penalties" for the Core-Elective conflict.

- **Old Logic:** `Sum(Core Vars) + Any(Elective Vars) <= 1`.
  - *Result:* If a Core was placed in a slot where an Elective *had* to go (due to other constraints), the solver would simply return `INFEASIBLE`.
- **New Logic:** `Sum(Core Vars) + Any(Elective Vars) > 1` implies `Conflict=True`.
  - `Minimize(Sum(Conflicts * 1000))`.
  - *Result:* The solver avoids conflicts if possible, but will return a valid schedule with a "conflict penalty" rather than failing completely. This allows the user to see *where* the problem is.

### C. Determinism
We observed that the scheduler was "randomly" failing or succeeding.
- **Fix:** Added strict sorting to `load_data`:
  - `rooms.sort(key=lambda x: x[0])` (by ID)
  - `courses.sort(key=lambda x: (x['name'], x['instance'], x['type']))`
  - This ensures that `c_idx=5` is *always* the same course across every run.

## 3. The "Lab in Amfi" Bug (Investigation & Fix)

### The Symptom
The user reported: "LAB CLASSES ARE IN AMFIS! THEORY CLASSES ARE IN LABS!" visually in the Calendar.

### The Investigation
1. **Hypothesis 1: Scheduler Constraint Failure?**
   - We verified `create_variables` logic. It was strict: `if is_lab_course and not is_lab_room: continue`.
   - We added `debug_assignments.py` to audit the database directly.
   - **Result:** The Database was **PERFECT**. Lab courses were in Lab rooms. Theory in Theory rooms.
   - *Contradiction:* The User still saw them wrong in the UI.

2. **Hypothesis 2: Display Logic Error?**
   - We inspected `models/schedule_model.py` -> `get_schedule_by_classroom`.
   - **The Bug:**
     ```sql
     -- OLD QUERY
     SELECT ... FROM Ders_Programi dp
     JOIN Dersler d ...
     WHERE d.teori_odasi = ? OR d.lab_odasi = ?  <-- ERROR
     ```
   - **Explanation:** This query asked: "Give me all scheduled sessions for any course that *defines* this room as its preferred room."
   - **Consequence:** If "Physics" defines "Amfi-1" as Theory Room and "Lab-1" as Lab Room:
     - The "Amfi-1" calendar would show **BOTH** the Physics Theory session (valid) **AND** the Physics Lab session (invalid ghost), because the Lab session belongs to "Physics", and "Physics" links to "Amfi-1".

### The Fix
We corrected the query to filter by the **actual assignment**:
```sql
-- NEW QUERY
SELECT ... FROM Ders_Programi dp
WHERE dp.derslik_id = ?  <-- CORRECT
```

## 4. Summary of Code Changes

| File | Change | Purpose |
| :--- | :--- | :--- |
| `controllers/scheduler.py` | **Robust Room Type Logic** | Added safe string normalization and strict Lab/Amfi exclusion rules. |
| `controllers/scheduler.py` | **Diagnostic Capacity** | Added "Lab vs Theory" capacity checks to console output. |
| `models/schedule_model.py` | **Fix `get_schedule_by_classroom`** | Switched from `WHERE d.room` to `WHERE dp.assignments`. |
| `controllers/scheduler.py` | **Stable Keys** | implemented `(Name, Instance, Type)` persistence. |
| `controllers/scheduler.py` | **Soft Constraints** | Converted Core-Elective hard conflict to high penalty. |

## 5. Next Steps
The Scheduler Core is now considered **Stable (v2.0)**.
- **Logic:** Verified.
- **Display:** Verified.
- **Persistence:** Verified.

Future work should focus on UI refinements (e.g., better conflict visualization) rather than scheduler logic.
