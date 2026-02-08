# Obsolete & Deprecated Functions Report

This document lists functions and methods identified as obsolete, deprecated, or dead code within the active codebase. These items are candidates for cleanup to improve code maintainability.

## 1. Controller Layer (`controllers/schedule_controller.py`)

| Function Name | Status | Reason |
| :--- | :--- | :--- |
| `handle_remove_course` | **Obsolete** | Marked as "Legacy". It uses the old string-parsing based removal logic. It has been superseded by `handle_remove_course_by_ids` which uses stable database IDs. |
| `export_schedule` | **Dead Code** | This method is a stub (`pass`) that calls `get_all_courses_as_string` but does nothing with the result. It is not connected to any UI action. |
| `import_schedule` | **Dead Code** | Empty stub method (`pass`) not connected to any UI action. |
| `validate_schedule` | **Dead Code** | Empty stub method (`pass`) returning an empty list. |

## 2. Model Layer (`models/schedule_model.py`)

| Function Name | Status | Reason |
| :--- | :--- | :--- |
| `remove_course` | **Deprecated** | Explicitly marked "DEPRECATED". It relies on unstable regex parsing of course strings. Only used by the obsolete `handle_remove_course` controller method. |
| `_has_slot_conflict` | **Unused** | Explicitly marked "DEPRECATED". It was kept for backward compatibility but is no longer called internally. Conflict logic is now handled by `ScheduleRepository` and `ScheduleService`. |
| `_check_time_conflict` | **Unused** | Explicitly marked "DEPRECATED". Similar to above, it is no longer used in the active codebase. |
| `_validate_course_data` | **Unused** | The logic for validating course data has been moved to `ScheduleService` (or `CourseInput` validation). This method is defined but never called. |
| `get_all_courses_as_string` | **Unused** | This method returns legacy string-formatted courses. It is only called by the dead `export_schedule` method in the controller. The application now uses `get_all_schedule_items` for structured data. |

## 3. View Layer (`views/schedule_view.py`)

| Function Name | Status | Reason |
| :--- | :--- | :--- |
| `add_course_to_list` | **Dead Code** | Empty method (`pass`) marked as "Legacy". The view now refreshes the entire table via `display_courses`. |
| `remove_course_from_list` | **Dead Code** | Empty method (`pass`) marked as "Legacy". |
| `get_current_selected_course` | **Dead Code** | Returns `None` and is marked "Legacy". Selection handling is now done directly within specific action handlers using item data. |
| `course_remove_requested` (Signal) | **Unused** | This signal is defined and connected, but never emitted. The view emits `course_remove_by_ids_requested` instead. |

## 4. Utilities (`utils/`)

| File/Module | Status | Reason |
| :--- | :--- | :--- |
| `fix_room_saturation.py` | **Unused** | This script appears to be a one-off fix that is not imported or used by the main application. It is likely safe to move to `scripts/debug` or `DEPRECATED`. |

## Recommendation

It is recommended to verify these findings and remove the code in a separate refactoring task. Since `OBSOLETE_FUNCTIONS.md` is now created, you can use it as a checklist for future cleanup.
