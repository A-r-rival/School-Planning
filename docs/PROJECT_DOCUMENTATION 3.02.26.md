# 📘 School Planner Project Documentation

## 1. Project Overview & Architecture

### 🎯 Overview
The School Planning application is a desktop tool designed to generate and manage course schedules for university departments. It utilizes a **Model-View-Controller (MVC)** architecture to ensure separation of concerns, maintainability, and scalability.

### 🏗️ Directory Structure
```
d:\Git_Projects\School-Planning\
├── models/                    # Model Layer (Data & Logic)
│   ├── schedule_model.py      # Database operations & Business logic
│   └── ...
├── views/                     # View Layer (UI)  
│   ├── schedule_view.py       # Main UI implementation (PyQt5)
│   └── ...
├── controllers/               # Controller Layer (Bridge)
│   ├── schedule_controller.py # Logic flow & Signal handling
│   ├── scheduler.py           # OR-Tools Optimization Logic
│   └── ...
├── docs/                      # Documentation
│   └── archive/               # Legacy documentation files
├── main.py                    # Application Entry Point
└── ...
```

### 🔄 MVC Workflow
1.  **User Interaction**: User clicks a button in the **View** (e.g., "Add Course").
2.  **Controller Action**: **View** emits a signal; **Controller** catches it and calls the appropriate method.
3.  **Model/Logic**: **Controller** invokes **Model** to update the database or run logic.
4.  **Feedback**: **Model** emits a signal (success/error) or returns data to the **Controller**, which updates the **View**.

---

## 2. Database Schema & Data Models

**Database File**: `okul_veritabani.db` (SQLite)

### Main Tables

#### 1. Dersler (Courses)
*   **Description**: The master list of all courses available to be scheduled.
*   **Code Access**: `models/schedule_model.py`
*   **Key Columns**:
    *   `ders_id` (PK): Unique ID.
    *   `ders_adi`: Name of the course.
    *   `teori_odasi`, `lab_odasi`: **FIXED** room assignments (if any).
    *   `akts`, `kredi`: Academic metadata.

#### 2. Ogretmenler (Teachers)
*   **Description**: Faculty members.
*   **Key Columns**: `ogretmen_num`, `ad`, `soyad`, `unvan`, `bolum_adi`.

#### 3. Ders_Programi (Scheduled Schedule)
*   **Description**: The result of the scheduling process (Active Schedule).
*   **Key Columns**:
    *   `program_id` (PK)
    *   `ders_adi`
    *   `ogretmen_id`
    *   `gun` (Day), `slot_baslangic`, `slot_bitis` (Time)
    *   `oda` (Room)

#### 4. Constraint Tables
*   **Ogretmen_Musaitlik**: Times when a teacher is **NOT** available.
*   **Ders_Ogretmen_Iliskisi**: Links courses to specific teachers.
*   **Ders_Sinif_Iliskisi**: Links courses to student groups (Department/Year/Pool).

---

## 3. Scheduling Logic: Resources & Constraints

This section details how the automated scheduler (`controllers/scheduler.py`) interprets data.

### 🏫 Resources
1.  **Classrooms (`Derslikler`)**:
    *   Loaded via `model.aktif_derslikleri_getir()`.
    *   Types: 'lab' or 'amfi'.
2.  **Time Slots**:
    *   Generated programmatically.
    *   Standard: 5 Days (Mon-Fri) × 8 Hours (09:00 - 17:00).

### 🔒 Constraints

#### 1. Fixed Room Assignments (⚠️ Critical)
*   **Source**: `Dersler` table (`teori_odasi`, `lab_odasi`).
*   **Behavior**: If a course has a value here, the scheduler **MUST** put it in that specific room.
*   **Risk**: High saturation (some rooms >85% load) caused previous failures.
*   **Code**: `controllers/scheduler.py` (lines ~88-99).

#### 2. Teacher availability
*   **Source**: `Ogretmen_Musaitlik` table.
*   **Behavior**: Hard constraint prevents assigning a teacher to a slot marked as unavailable.

#### 3. Conflicts (Hard Constraints)
*   **Teacher Conflict**: A teacher cannot be in two places at once.
*   **Student Group Conflict**: A generic student group (e.g., "Computer Eng. 1st Year") cannot have overlapping courses.
*   **Room Conflict**: A room can only hold one course per slot.

---

## 4. Development Guide

### How to Run
```bash
python main.py
```

### Adding New Features
1.  **Model**: Implement the data logic in `models/schedule_model.py`.
2.  **View**: Add UI elements in `views/schedule_view.py`.
3.  **Controller**: Connect View signals to Model functions in `controllers/schedule_controller.py`.

### Debugging/Analysis Tools
*   `Schedule Creation v1/`: Contains standalone scripts for testing scheduler logic (`run_scheduler.py`, `check_schema.py`).
*   `utils/`: Helper scripts for data fixing (`fix_room_saturation.py`).

---

## 5. Historical Record: Fixes & Walkthroughs

> Preserved logs of critical debugging sessions and fixes.

### 🛠️ 2025-12-21: Scheduler Refactor ("Option A")
**Problem**: The scheduler code was messy, had duplicate methods, and inconsistent time parsing, causing crashes and valid schedules to be rejected.
**Fixes**:
1.  **Clean Code**: Removed duplicate `add_hard_constraints`.
2.  **Time Parsing**: Implemented robust `HH:MM` -> minutes conversion.
3.  **Strict Logic**: Enforced strict room checks (`sum(slots) == duration`).
4.  **Result**: Successfully generated valid schedules in "Strict Mode" (first pass).

### 🛠️ 2025-12-21: Data Deduplication Fix
**Problem**: "Strict" and "Relax Teacher" modes failed, but "Relax Rooms" worked.
**Root Cause**: A `LEFT JOIN` bug in `fetch_all_course_instances` caused courses with multiple student groups to be duplicated in the scheduler input (e.g., "Math 101" appeared 3 times if it had 3 groups). This artificially tripled the demand for rooms, making the schedule mathematically impossible.
**Fix**:
*   Refactored data fetching to **Group By** Course.
*   Aggregated student groups into a list attached to a single Course object.
*   **Result**: Room loads dropped from >100% to ~75%, allowing strict constraints to pass.

### 🛠️ 2025-12-20: Hukuk-101 Saturation Fix
**Problem**: The room **'Hukuk-101'** had exactly 40 hours of courses assigned (100% capacity).
**Impact**: Any teacher unavailability overlapping with this room caused immediate failure.
**Fix**:
*   Ran `utils/fix_room_saturation.py`.
*   Removed fixed room assignments for ~11 hours of courses in that room.
*   **Result**: Load dropped to ~72%, restoring flexibility.
