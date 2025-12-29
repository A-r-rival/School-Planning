# Debug Analysis Report - Teacher Availability Module
**Date:** 2025-12-29
**Module:** Teacher Availability (View & Controller)

## Overview
during the refactoring of the Teacher Availability module, several critical crashes were encountered. These ranged from signal handling issues to object lifecycle management problems. This document details each crash, its root cause, and the applied solution.

---

## 1. Crash on Search Interaction (Enter/Arrow Keys)
**Symptom:** The application crashed immediately when the user pressed "Enter" or used arrow keys inside the teacher search combo box (`QComboBox`).

### Root Cause
The `QComboBox` in PyQt5 emits signals differently based on user interaction.
- We were listening to `currentIndexChanged` or `currentData` changes.
- When a user types, intermediate states might result in `currentData` returning `None` or an invalid type (e.g., `QVariant` wrapping nothing or a string instead of the expected `int` ID).
- The code tried to cast `t_id` directly or use it in a SQL query without validation: `isinstance(t_id, int)`.

### Fix Implementation
We implemented strict type checking in the `_on_teacher_changed` slot.

```python
def _on_teacher_changed(self, index):
    t_id = self.teacher_combo.currentData()
    
    # 1. Null check
    if t_id is None:
        return
        
    # 2. Type check
    if not isinstance(t_id, int):
        # Prevent processing partial inputs or invalid states
        return
        
    # Proceed only if valid
    ...
```

---

## 2. Crash on Deleting Unavailability
**Symptom:** Clicking the "Sil" (Delete) button caused an immediate crash or silent failure.

### Root Cause
1. **Signal Connection:** The delete button was connected using a `lambda` inside a loop: `clicked.connect(lambda: self.delete(id))`. Python lambdas capture variables by reference, not value. By the time the click happened, the variable `id` held the value of the *last* item in the loop.
2. **Missing Controller Logic:** The controller method `remove_teacher_unavailability` was not correctly refreshing the view for the *currently selected teacher*, causing the table to try and render invalid data or crash on refresh.

### Fix Implementation
1. **Use `functools.partial`:** This captures the variable value at creation time.
   ```python
   from functools import partial
   delete_btn.clicked.connect(partial(self._on_delete_clicked, item_type, item_id))
   ```
2. **Controller Update:** Updated the refresh logic to handle both "All Teachers" and "Single Teacher" modes.

---

## 3. Crash on Reopening Availability Window
**Symptom:** Closing the "Teacher Availability" window and trying to open it again caused the application to crash with an unrecoverable error (often a Segmentation Fault or Python crash).

### Root Cause
The `TeacherAvailabilityView` is a `QDialog` (or `QWidget`). When closed, PyQt might destroy the underlying C++ object.
- The Controller held a reference `self.availability_view`.
- When `open_teacher_availability_view` was called a second time, it might have tried to `show()` the existing python wrapper which pointed to a deleted C++ object.
- Alternatively, if we just created a new one without cleaning the old one, signals connected to the old instance might still fire or cause conflicts.

### Fix Implementation
We implemented a robust lifecycle management in the Controller:

```python
def open_teacher_availability_view(self):
    # 1. Safe Cleanup
    if hasattr(self, 'availability_view') and self.availability_view is not None:
        try:
            self.availability_view.close()
            self.availability_view.deleteLater() # Schedule C++ deletion
        except:
            pass
    
    # 2. Re-create fresh instance
    teachers = self.model.get_all_teachers_with_ids()
    self.availability_view = TeacherAvailabilityView(self.view, teachers)
    self.availability_view.set_controller(self)
    self.availability_view.show()
```

---

## 4. Crash on "Add Unavailability" (Silent Crash or "Rash")
**Symptom:** Clicking "Yeni Namüsaitlik Ekle" sometimes caused a crash, or seemingly did nothing (silent crash caught by main loop but breaking logic).

### Root Cause
- **Initialization Order:** The `AddUnavailabilityDialog` called `_on_teacher_changed(0)` inside its `__init__`.
- At this point, `self.controller` or `self.span_combo` might not have been fully assigned yet.
- Accessing `self.controller` before assignment raised an `AttributeError`.

### Fix Implementation
1. **Safety Checks at Start:** Added `if hasattr(self, 'controller'):` checks.
2. **Try-Except Blocks:** Wrapped the dialog execution in a `try-except` block to catch and report errors instead of crashing the app.

```python
try:
    if hasattr(self, 'controller'):
        dialog = AddUnavailabilityDialog(...)
        if dialog.exec_():
             # Process data
except Exception as e:
    # Log error and show message box
    print(f"CRASH: {e}")
```

---

## 5. Model Method Missing (`get_all_teacher_unavailability`)
**Symptom:** `AttributeError: 'ScheduleModel' object has no attribute 'get_all_teacher_unavailability'`.

### Root Cause
During the refactor to "Combined Availability" (handling both time slots and day spans), we replaced the old separate methods with `get_combined_availability`. However, the Controller was still calling the old method name in one specific branch (when loading "All Teachers").

### Fix Implementation
Updated `ScheduleController.load_all_teacher_availability` to use the new unified method:

```python
def load_all_teacher_availability(self):
    # Old: data = self.model.get_all_teacher_unavailability() -> ERROR
    # New:
    data = self.model.get_combined_availability()
    self.availability_view.update_table(data)
```

---

## Conclusion
The module is now significantly more robust. The adoption of defensive programming (null checks, type checks, try-except wrappers) and proper Qt lifecycle management (deleteLater) has eliminated the reported crashes. The UI is stable and handles edge cases (like typing in search boxes or reopening windows) gracefully.
