# UI Refactoring & Filter Implementation Archive (22.12.25)

This folder contains detailed records of the work done to refactor the User Interface and implement advanced filtering for the Schedule Management system.

## Files

1.  **[01_ui_refactoring.md](01_ui_refactoring.md)**
    - Details the separation of "Add Course" into a `QDialog`.
    - Explains layout changes (Window resize, button organization).
    - Covers the removal of inline input fields.

2.  **[02_filter_implementation.md](02_filter_implementation.md)**
    - Details the implementation of "Day", "Course Search", and "Teacher Search" filters.
    - Explains backend Model updates to query `Ders_Programi` for rich data (Time/Day).
    - Covers the standardization of course string formats and controller logic.

## Key Outcomes
- **Cleaner UI:** Main window is less cluttered and more focused on the list view.
- **Better UX:** Course addition is focused in a dialog with validation.
- **Powerful Filtering:** Users can now slice the schedule data by practically any dimension (Faculty, Dept, Year, Day, Teacher, Name).
- **Stability:** Fixed crashes related to removed UI elements.
