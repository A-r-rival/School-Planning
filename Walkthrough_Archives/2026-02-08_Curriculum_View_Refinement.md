# Walkthrough: Multiple Teachers per Course & Template Management

We have successfully implemented the ability to assign specific teachers to specific course sections (instances) and restructured the course addition workflow.

## Key Features Added

### 1. Split "Add Course" Workflow (Refined)
The "Course Operations" area in `ScheduleView` has been reorganized into two distinct groups:

*   **Müfredat İşlemleri**:
    *   **📝 Müfredata Ekle/Çıkar**: Adds a template definition to the curriculum. Now supports **Pool Courses**.
    *   **👀 Müfredatı Görüntüle**: Opens a table view of all curriculum courses.
        *   **Grouping**: Courses are grouped by **Class Year** (1. Sınıf, 2. Sınıf...) with distinct headers. 
            *   **Core Courses** have a **Light Blue** banner.
            *   **Pool Courses** are grouped by their specific Pool Code (e.g., SDII, SDP) with **unique pastel colored** banners.
        *   **Filters**: You can filter by Faculty, Department, and specifically select a Class Year or "Havuz Dersleri".
        *   **Advanced Filtering**:
            *   **Ders Tipi**: Quickly filter between "Hepsi", "Sadece Zorunlu", or "Sadece Seçmeli (Havuz)".
            *   **Havuz Kontrolü**: When a **Department** is selected, a new filter row appears allowing you to toggle specific Pools on/off.
    
*   **Program (Ad Hoc) İşlemleri**:
    *   **➕ Sadece Bu Dönemki Programa Ekle**: Adds a single usage to the schedule manually (renamed for clarity).
    *   **➖ Seçili Dersi Sil**: Removes a selected course from the schedule.

### 2. Support for Pool Courses (Havuz Dersleri)
When defining a new curriculum template ("Müfredata Ekle"):
*   **New Option**: You can now choose between **"Sınıfa Zorunlu Ekle"** (Standard) and **"Havuza Ekle"** (Pool).
*   **Havuz Kodu**: If "Havuza Ekle" is selected, you must specify a **Pool Code** (e.g., `MÜH`, `SOS`).
*   **Effect**: 
    *   **Class Course**: Linked to a specific Class Year (e.g., Computer Eng. Year 1).
    *   **Pool Course**: Linked to the Department and Pool Code, allowing multiple departments to share the same pool requirement.

### 3. Teacher Course Assignments (Section Support)
You can now assign specific teachers to specific sections (instances) of a course.

*   **Location**: "Öğretmen Müsaitlik ve Ders Atamaları" window.
*   **New Tab**: "Ders Atamaları".
*   **How to Use**:
    1.  Select a Teacher from the top dropdown.
    2.  Select a Course from the "Ders" dropdown (loaded from Curriculum).
    3.  Specify the **Şube (Instance)** number (e.g., 1 for Group A, 2 for Group B).
    4.  Click **"Ata"**.
    
*   **Result**: The Auto-Scheduler will respect these assignments, ensuring that "Advanced English (Instance 1)" goes to Teacher A, and "Advanced English (Instance 2)" goes to Teacher B.

### 3. Quick-Add Template Shortcut
Inside the Teacher Availability view, you can click the **"📝 Yeni Tanımla"** button to quickly add a missing course template to the curriculum without leaving the assignment screen.

## Technical Changes
*   **Database**: Confirmed `Ders_Ogretmen_Iliskisi` supports `(ders_instance, ders_adi, ogretmen_id)` key.
*   **Scheduler Logic**: Updated `scheduler_services.py` to map teachers using `(course_name, instance)` instead of just `course_name`.
*   **Data Persistence**: Fixed issue where manual teacher assignments were not saving to the requirements table.

## Verification
A backend verification script (`tests/verify_teacher_assignment.py`) was run to confirm:
1.  Successful addition of Template courses to the database.
2.  Successful linking of Teachers to specific Course Instances.
3.  Persistence of these links in the database.
