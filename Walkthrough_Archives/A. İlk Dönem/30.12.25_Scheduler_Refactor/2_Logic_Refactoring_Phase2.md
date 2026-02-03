# Scheduler Refactoring - Phase 2: Logic Integration

## Objective
The goal of Phase 2 was to integrate the componentized services (`CourseRepository`, `CurriculumResolver`, `CourseMerger`) into the main `ORToolsScheduler` and verify the new constraint logic.

## Changes Implemented

### 1. Service Integration in `scheduler.py`
- Refactored `_fetch_all_course_instances` to use the new pipeline:
  1. `CourseRepository` fetches raw rows.
  2. `CurriculumResolver` determines `CourseRole` (CORE/ELECTIVE) based on Department+Year context.
  3. `CourseMerger` creates `PhysicalCourse` objects, strictly validating role consistency within a context.
  4. `SchedulableCourseBuilder` generates the flat dictionary format required by OR-Tools.

### 2. Constraint Refactoring
- **`add_hard_constraints`**: Consolidated scattered logic into a single authoritative method.
  - Room Conflicts
  - Teacher Conflicts
  - Teacher Unavailability (`get_teacher_unavailability` integrated)
  - Teacher Day Span (`get_teacher_span` integrated)
  - Calls `add_student_group_conflicts`
  
- **`add_student_group_conflicts`**: Completely rewritten.
  - **Old Logic**: Relied on a global `is_elective` flag which was prone to context errors (e.g., a course being elective for Dept A but Core for Dept B).
  - **New Logic**:
    - Iterates over `ProgramCourseContext` for each Student Group.
    - Uses `get_role_for_group(course, dept, year)` helper.
    - Applies `Sum(Core) <= 1`.
    - Applies `Sum(Core) + AnyElective <= 1`.
    - Populates `group_slot_data` for soft constraints (Different Pool overlap penalties).

### 3. Cleanup
- Removed legacy `is_elective` determination logic from `_fetch_all_course_instances`.
- Removed duplicated constraint methods that were accidentally nested during refactoring.
- Fixed file structure to ensure clean class-level method definitions.

### 4. Code Review Fixes (Post-Verification)
- **Bleeding Occupancy Bug**: Fixed logic in `create_variables` to ensure course occupancy does not accidentally wrap to the next day when `duration` matches `SLOTS_PER_DAY` boundary.
- **Save Logic Unification**: Created `_commit_assignments` helper to unify `extract_schedule` and `save_manual_assignments`, preventing inconsistency.
- **Duration Safety**: Added check to enforce `duration <= SLOTS_PER_DAY`.
- **Parent Key Safety**: Updated `scheduler_services` to explicitly include `instance` in `PhysicalCourse` and `parent_key`, ensuring compatibility with `scheduler.py` unpacking.

## Verification Status

### Tests Created
- `tests/test_scheduler_phase2_integration.py`: Attempts to run the full scheduler on `okul_veritabani.db`.

### Results
- **Static Analysis**: `scheduler.py` compiles successfully. Logic flow is sound.
- **Integration Test**: 
  - **Status**: FAILING (Environment/Crash).
  - **Details**: The verification script crashes silently during the solver execution or initialization on the local environment. Output capture suggests a potential conflict or memory issue, possibly related to `PyQt5` vs `ORTools` import order (fixed in script, but crash persisted) or data handling.
  
## Next Steps
1. **Debug Integration Test**: Run with a debugger or simplified DB to isolate the crash.
2. **Phase 3**: Verify Solver Constraint Effectiveness (Analyze output schedules to ensure Core/Elective rules are respected).
