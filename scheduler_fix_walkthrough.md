# Scheduler Fixes Walkthrough (Investigation & Resolution)

## Overview
This document summarizes the investigation and fixes applied to resolve the scheduler's "Infeasible" status and crashes. The primary goal was to enable room preferences and generate a valid schedule despite strict constraints.

## 1. Initial Infeasibility: Test Harness Bug 🐛
**Issue**: The scheduler was consistently returning `INFEASIBLE` even when constraints were disabled.
**Root Cause**: The testing script `test_scheduler_headless.py` was manually calling `load_data()` and `create_variables()` **before** `scheduler.solve()`. Since `solve()` also calls these methods internally, it led to stale variable references and phantom infeasibility.
**Fix**:
- Updated `test_scheduler_headless.py` to remove manual calls.
- Created cleaner validation script `scripts/debug/test_scheduler_binary.py`.
- **Result**: Baseline scheduler (without room preferences) successfully scheduled all 241 courses.

## 2. Data Integrity: Missing Floor Data 🏗️
**Issue**: Teacher requests for specific floors (e.g., "Kat 2") resulted in zero matching rooms.
**Root Cause**: The `floor` column in the `Derslikler` table was added via migration with `DEFAULT 0` but never populated. All 78 rooms were effectively on "Floor 0".
**Fix**:
- Created `scripts/debug/populate_floors.py` to distribute rooms based on naming conventions.
- **Result**:
  - **Floor 0**: 26 rooms (including Amfi-1, Amfi-2)
  - **Floor 1**: 26 rooms
  - **Floor 2**: 26 rooms (including Amfi-3, Amfi-4)

## 3. Floor Preferences & Lab Distribution 🧪
**Issue**: Even with valid floor data, enabling room preferences caused infeasibility.
**Root Cause**: Lab rooms were unevenly distributed (mostly on Floor 1), making it impossible for teachers to request a specific floor if that floor had no labs available.
**Fix**:
- Updated `populate_floors.py` to redistribute labs evenly:
  - **Floor 0**: Labs 1-3
  - **Floor 1**: Labs 4-7
  - **Floor 2**: Labs 8-10
  - All floors now have at least 2 labs to accommodate preferences.

## 4. Logic Bug: Lab Preferences applied to Theory Courses 🧠
**Issue**: Teachers requesting "Lab" were unable to schedule their **Theory** courses (e.g., "Analiz I"). 
**Root Cause**: The logic in `add_teacher_room_preferences` applied the "Lab" constraint to **ALL** courses taught by the requesting teacher. This forced theory courses into labs, which is invalid (theory courses cannot use labs).
**Fix**:
- Modified `scheduler.py` to check `course['type']` before applying the lab preference constraint.
- Teacher "Lab" preference now **only** restricts lab-type courses to lab rooms. Theory courses remain flexible.

## 5. Remaining Issue: Capacity / Pre-Assignment Constraints 🚧
**Current Status**: 
- Scheduler returns `INFEASIBLE`.
- Debug logs show **71 courses** have **ZERO viable rooms** when room preferences are enabled.
- **Critical Finding**: Most courses report having only **1 viable room** *before* teacher preferences are applied.
  - Example: Course "Analiz I" shows `Viable rooms BEFORE teacher pref: 1`.
  - This single room is likely determined by strict **Capacity Filtering** or legacy `fixed_room` assignments (even if implicit).
- **The Conflict**: When a course is forced into exactly 1 specific room (due to capacity/type), and the teacher requests a floor that doesn't match that room, the result is ZERO options → Infeasibility.

## Next Steps Recommended
1. **Verify Capacity Constraints**: Check if courses have strict `group_size` matching room `capacity` exactly, limiting options to a single room.
2. **Review Fixed Assignments**: Ensure no hidden `fixed_room` values are influencing variable creation.
3. **Soft Constraints**: Implement teacher preferences as soft constraints (penalties) so the solver can prioritize feasibility over preferences if conflicts persist (especially for teachers with disabilities, using high penalties).
