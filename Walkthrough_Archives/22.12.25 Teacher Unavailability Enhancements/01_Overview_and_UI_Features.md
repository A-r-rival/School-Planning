# Teacher Unavailability - UI Enhancements and Features

## Overview
This document details the enhancements made to the "Teacher Unavailability" (Öğretmen Namüsaitlik Durumu) module. The goal was to transform a basic data entry form into a fully interactive management system allowing users to view, add, edit, and delete unavailability slots for all teachers.

## Key Features Implemented

### 1. "All Teachers" View
*   **Problem:** Users could only view one teacher's unavailability at a time, making it difficult to get a global overview of constraints.
*   **Solution:** Added a "Tüm Öğretmenler" (All Teachers) option to the teacher selection dropdown.
*   **Implementation:**
    *   The `TeacherAvailabilityView` was updated to include an entry with ID `-1` and text "Tüm Öğretmenler".
    *   When selected, the view triggers a specific load method in the controller (`load_all_teacher_availability`) that fetches data for every teacher.
    *   **Visual Logic:** The "Müsait Değil Ekle" (Add Unavailability) button is disabled in this mode to prevent ambiguity about which teacher is being modified.

### 2. Dynamic Column Headers and Content
*   **Problem:** The table structure needed to adapt based on the context. When viewing a specific teacher, the "Teacher Name" is redundant, but the "Reason" is important. When viewing all teachers, "Teacher Name" is critical.
*   **Solution:** Implemented dynamic column switching.
*   **Implementation:**
    *   **Column 0:**
        *   **Context:** Specific Teacher Selected -> Header: "Açıklama" (Reason/Description) -> Content: The `aciklama` text.
        *   **Context:** All Teachers Selected -> Header: "Öğretmen" (Teacher) -> Content: The teacher's name.
    *   **Code Snippet (`teacher_availability_view.py`):**
        ```python
        if self.current_teacher_id == -1:
            self.table.setHorizontalHeaderItem(0, QTableWidgetItem("Öğretmen"))
            # ... set text to teacher_name
        else:
            self.table.setHorizontalHeaderItem(0, QTableWidgetItem("Açıklama"))
            # ... set text to description
        ```

### 3. Styled "Actions" Column
*   **Problem:** The "Edit" (Düzenle) and "Delete" (Sil) buttons looked cluttered and were hard to distinguish from data.
*   **Solution:** Created a dedicated container for buttons with custom styling.
*   **Implementation:**
    *   Used a `QWidget` as a container inside the table cell.
    *   Applied a horizontal layout (`QHBoxLayout`) with minimal margins.
    *   **Styling:**
        *   Background Color: Light Blue (`#e6f3ff`)
        *   Border Radius: `4px`
        *   Button Styling: White background, distinct borders, and hover effects.
    *   **Result:** The "İşlem" column is visually distinct, guiding user interaction.

### 4. Tooltip for Disabled State
*   **Feature:** To improve UX, when the "Add" button is disabled (during "All Teachers" view), hovering over it displays a tooltip explaining why.
*   **Message:** "İlk önce filtreden öğretmen seçiniz" (Please select a teacher from the filter first).

## Design Decisions
*   **Window Size:** Increased default size to 800x600 to accommodate the extra columns and data.
*   **Column Resizing:**
    *   "Öğretmen/Açıklama" (Col 0): `Stretch` (Takes all remaining space).
    *   "Gün" (Col 1): Fixed 120px.
    *   "Başlangıç" (Col 2): Fixed 80px.
    *   "Bitiş" (Col 3): Fixed 80px.
    *   "İşlem" (Col 4): Fixed 160px.
    *   *Rationale:* Ensures timestamps and action buttons are always visible and aligned, while the variable-length text (Name/Description) expands.

## Summary of Files Modified
*   `views/teacher_availability_view.py`: Heavy modifications for UI logic, event handling, and layout management.
