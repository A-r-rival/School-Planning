# Reorganization of 'Schedule Creation v1'

**Date:** 2026-02-03
**Status:** Executed

## Goal Description
The user wants to break up the "Schedule Creation v1" folder. This folder contains a mix of debug scripts, runners, and data helpers. We will move them to more semantic locations within the project structure to improve maintainability.

## Implementation Details

### 1. Move Debug & Verification Tools
Destination: `scripts/debug/`
*   `debug_calendar_flow.py`
*   `debug_db_dump.py`
*   `debug_ui_logic.py`
*   `check_schema.py`
*   `verify_prerequisites.py`
*   `verify_schedule.py`

### 2. Move Runner & Setup Scripts
Destination: `scripts/` (Root of scripts)
*   `run_scheduler.py`
*   `assign_teachers.py`
*   `fix_missing_departments.py`

### 3. Handle Conflicting/Test Scripts
*   `populate_classrooms.py` -> `scripts/debug/setup_test_rooms.py` (Renamed to avoid conflict with existing `scripts/populate_rooms.py`)
*   `test_ortools_*.py` -> `tests/legacy/` (Created to keep them separate from main pytest suite)

### 4. Delete Old Folder
*   Removed `Schedule Creation v1/`

## Rationale
*   `scripts/`: Appropriate for executable runners.
*   `scripts/debug/`: Appropriate for inspection tools.
*   `tests/legacy/`: Appropriate for old, unmaintained tests.
