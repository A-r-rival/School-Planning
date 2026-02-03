# Resources and Constraints Location Guide

This document shows where all resources and constraints are stored in your School Planning project.

## 📊 Database
**`okul_veritabani.db`**  
All your resources and constraints are stored in this SQLite database file.

## 🏫 RESOURCES (What you have available)

### 1. Classrooms/Rooms (`Derslikler` table)
*   **Columns**: `derslik_num`, `derslik_adi`, `tip`, `kapasite`, `silindi`
*   **Current**: 20 active rooms
*   **Types**: 'lab' or 'amfi'
*   **View in code**: `models/schedule_model.py` → `aktif_derslikleri_getir()`

```python
# Access rooms
rooms = model.aktif_derslikleri_getir()
# Returns: [(derslik_num, derslik_adi, tip, kapasite), ...]
```

### 2. Teachers (`Ogretmenler` table)
*   **Columns**: `ogretmen_num`, `ad`, `soyad`, `unvan`, `bolum_adi`
*   **View in code**: `models/schedule_model.py` → `get_all_teachers_with_ids()`

```python
# Access teachers
teachers = model.get_all_teachers_with_ids()
# Returns: [(ogretmen_num, "ad soyad"), ...]
```

### 3. Courses (`Dersler` table)
*   **Columns**: `ders_kodu`, `ders_instance`, `ders_adi`, `teori_odasi`, `lab_odasi`, `akts`
*   **Current**: 616 courses need to be scheduled
*   **Note**: `teori_odasi` and `lab_odasi` contain FIXED ROOM assignments.
*   **View in code**: `controllers/scheduler.py` lines 68-103 (`_fetch_all_course_instances`)

```python
# Scheduler loads courses
courses = scheduler._fetch_all_course_instances()
```

### 4. Time Slots (Generated in code)
*   **Description**: Not in database - generated programmatically
*   **Location**: `controllers/scheduler.py` → `load_data()` (lines 52-66)
*   **Definition**: 5 days × 8 hours = 40 slots per week
    *   **Days**: Pazartesi, Salı, Çarşamba, Perşembe, Cuma
    *   **Hours**: 09:00-17:00 (8 slots)

---

## 🔒 CONSTRAINTS (Rules that must/should be followed)

### 1. Fixed Room Assignments (⚠️ MAIN ISSUE)
*   **Location**: `Dersler` table → `teori_odasi` and `lab_odasi` columns
*   **Problem**: 542 out of 616 courses have fixed rooms assigned.
*   **Impact**: Creating severe room saturation (85%+ for some rooms).
*   **Code check**:
    ```sql
    SELECT COUNT(*) FROM Dersler 
    WHERE teori_odasi IS NOT NULL OR lab_odasi IS NOT NULL;
    -- Returns: 542 courses
    ```
*   **Files that use this constraint**:
    *   `controllers/scheduler.py` lines 88-99 (reads fixed rooms)
    *   `controllers/scheduler.py` lines 117-119 (filters rooms based on fixed assignment)

### 2. Teacher Unavailability
*   **Location**: `Ogretmen_Musaitlik` table
*   **Columns**: `id`, `ogretmen_id`, `gun`, `baslangic`, `bitis`
*   **Meaning**: Time slots when teachers are NOT available.
*   **Access**: `models/schedule_model.py` → `get_teacher_unavailability()` (lines 835-856)

```python
# Get teacher unavailable times
unavail = model.get_teacher_unavailability(teacher_id)
# Returns: [(gun, baslangic, bitis, id), ...]
```
*   **Used in scheduler**: `controllers/scheduler.py` lines 207-230.

### 3. Teacher-Course Assignment
*   **Location**: `Ders_Ogretmen_Iliskisi` table
*   **Columns**: `ders_adi`, `ders_instance`, `ogretmen_id`
*   **Ensures**: Each course has an assigned teacher.

### 4. Student Group-Course Assignment
*   **Location**: `Ders_Sinif_Iliskisi` table
*   **Columns**: `ders_adi`, `ders_instance`, `donem_sinif_num`
*   **Prevents**: Student group conflicts (same group can't have 2 courses at same time).

---

## 🔧 How to Modify Resources/Constraints

### Option 1: Directly Edit Database
```bash
# Open database in SQLite browser or command line
sqlite3 okul_veritabani.db
```
```sql
-- Example: Remove fixed room from a course
UPDATE Dersler SET teori_odasi = NULL WHERE ders_adi = 'CourseNameHere';

-- Example: Clear ALL fixed rooms (drastic!)
UPDATE Dersler SET teori_odasi = NULL, lab_odasi = NULL;
```

### Option 2: Through Application Code

**Add/Remove Rooms**:
```python
# models/schedule_model.py
model.derslik_ekle("NewRoom", "amfi", 100)  # Add room
model.derslik_sil(derslik_num)  # Soft delete room
```

**Modify Teacher Unavailability**:
Currently no direct method - need to execute SQL directly:
```python
model.c.execute("DELETE FROM Ogretmen_Musaitlik WHERE ogretmen_id = ?", (teacher_id,))
model.conn.commit()
```

---

## 📁 Key Project Files

### Core Scheduler Files
1.  **`controllers/scheduler.py`** - Main OR-Tools scheduler implementation
    *   Lines 40-66: Loads resources (rooms, courses, teachers)
    *   Lines 105-141: Creates variables (respects fixed room constraint)
    *   Lines 143-230: Adds hard constraints
    *   Lines 232-267: Smart retry mechanism
2.  **`models/schedule_model.py`** - Database operations
    *   Lines 26-38: Database connection setup
    *   Lines 796-799: Get active rooms
    *   Lines 472-479: Get all teachers
    *   Lines 835-856: Get teacher unavailability
3.  **`main.py`** - Application entry point

### Database Files
*   `okul_veritabani.db` - Main database (THIS IS WHERE EVERYTHING IS STORED)
*   `populate_students.py` - Script that initially populated students/courses
*   `parse_curriculum.py` - Script that parsed curriculum data

### Diagnostic Files
*   `analyze_infeasibility.py` - Analysis script
*   `quick_room_check.py` - Quick room saturation check
*   `debug_constraints.py` - Debug constraints
*   `find_saturated_rooms.py` - Find over-saturated rooms

---

## 🎯 Current Bottlenecks (Based on Analysis)

1.  **Fixed Rooms** (`Dersler.teori_odasi`, `Dersler.lab_odasi`)
    *   542/616 courses have assignments.
    *   Top rooms: 65-88% saturated.
    *   This was the primary reason Attempts 1 & 2 failed.

2.  **Teacher Unavailability** (`Ogretmen_Musaitlik`)
    *   Secondary issue.
    *   Combined with fixed rooms = infeasible.

3.  **Time Slots** (hardcoded: 8 hours/day)
    *   Could extend to 9-10 hours if needed.
    *   Modify in `controllers/scheduler.py` line 54.

---

## 💡 Quick Fixes

### Fix 1: Clear Fixed Rooms for Non-Lab Courses
```python
# Run in Python console or create script
import sqlite3
conn = sqlite3.connect('okul_veritabani.db')
c = conn.cursor()
# Only keep lab rooms for actual lab courses, clear theory rooms
c.execute("UPDATE Dersler SET teori_odasi = NULL")
conn.commit()
conn.close()
```

### Fix 2: Add More Time Slots
Edit `controllers/scheduler.py` line 54:
```python
# Change from:
hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00']
# To (9 hours instead of 8):
hours = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00']
```

### Fix 3: Add More Rooms
```python
# Add virtual/flexible rooms
model.derslik_ekle("Esnek-1", "amfi", 50)
model.derslik_ekle("Esnek-2", "amfi", 50)
# etc...
```
