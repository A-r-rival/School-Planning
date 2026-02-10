# Phase 1: Scheduler Component Extraction & Services

**Date:** 30.12.2025
**Status:** ✅ Completed

## 🎯 Objective
To decouple the business logic of course fetching, merging, and context resolution from the `ORToolsScheduler`. The monolithic `_fetch_all_course_instances` method was too complex, making it impossible to debug why certain courses were flagged as "Elective" or "Core" incorrectly.

## 🏗️ Solution: Service Architecture
We extracted the logic into four distinct layers in `controllers/scheduler_services.py`:

### 1. `CourseRepository` (Data Layer)
*   **Responsibility:** Fetch raw rows from the database.
*   **Key Change:** No logic, just SQL. Returns `RawCourseRow` objects.
*   **Benefit:** We can see exactly what comes out of the DB without interference.

### 2. `CurriculumResolver` (Business Logic)
*   **Responsibility:** Determine if a course is CORE or ELECTIVE for a specific program (Department + Year).
*   **Key Logic:**
    *   Uses `curriculum_data.py` strictly.
    *   If a course name matches a pool entry -> `ELECTIVE`.
    *   Otherwise -> `CORE`.
*   **Win:** Removing the fuzzy `is_elective` flag logic that guessed based on names.

### 3. `CourseMerger` (Physical Layer)
*   **Responsibility:** Merge duplicate database rows (same course for different student groups) into a single `PhysicalCourse`.
*   **Key Change:** The unique key is now `(Name, Teachers, T, U, L)`.
*   **Critical Innovation:** A single physical course now holds a **Set of Contexts**.
    *   *Context A:* Computer Eng - Year 4 - **CORE**
    *   *Context B:* Industrial Eng - Year 4 - **ELECTIVE (Pool SDIII)**
*   **Validation:** Ensures no single student group sees conflicting roles for the same course.

### 4. `SchedulableCourseBuilder` (Adapter Layer)
*   **Responsibility:** Convert `PhysicalCourse` objects into the dictionary format required by OR-Tools.
*   **Output:** Removes `is_elective` flag, replaces it with `program_contexts` list.

## 🧪 Verification: The "Golden Case"
We created a specialized unit test `tests/test_scheduler_refactor.py` to verify the "Golden Case":
> *A single course that is mandatory for one department but elective for another.*

**Test Scenario:**
*   **Course:** "Machine Learning"
*   **Dept 1 (CSE):** Not in pool -> Resolved as **CORE**.
*   **Dept 2 (IE):** In 'SDIII' pool -> Resolved as **ELECTIVE**.
*   **Result:** The merger produced a SINGLE `PhysicalCourse` object containing BOTH contexts correctly.

## 📂 New Files
*   `controllers/scheduler_services.py`
*   `tests/test_scheduler_refactor.py`

## 🔜 Next Steps (Phase 2)
Integrate these services into `scheduler.py` and rewrite the constraint logic (`add_student_group_conflicts`) to utilize the new `program_contexts` instead of `is_elective`.
