# Scripts Cleanup, Curriculum Relocation and SQL Fixes

This update focuses on stabilizing the application by relocating data sources, fixing broken imports, resolving SQL errors, and cleaning up the `scripts/` directory to ensure all tools function correctly with the new project structure.

## Key Changes

### 1. Curriculum Data Relocation
To centralize data management, the curriculum data sources were moved from the `scripts/` folder to the `database/` package:
*   **Moved**: `scripts/curriculum_data.py` -> `database/curriculum_data.py`.
*   **Moved**: `Curriculum/` folder -> `database/Curriculum/`.
*   **Action**: Created `database/__init__.py` to establish it as a proper Python package.

### 2. Import & Path Fixes
Following the relocation, extensive updates were made to ensure all parts of the application could locate the data:
*   **Import Updates**: Modified `scheduler.py`, `scheduler_services.py`, `calendar_view.py`, and `calendar_schedule_builder.py` to import from `database.curriculum_data` instead of `scripts`.
*   **Path Standardization**: Fixed hardcoded database paths in `populate_rooms.py`, `export_pool_relationships.py`, `generate_rich_docs.py`, `assign_teachers.py`, and debug scripts. They now reliably point to `database/okul_veritabani.db`.

### 3. SQL Error Resolution
Resolved a critical error causing the Curriculum View to appear empty:
*   **Error**: `no such column: dhi.bolum_num` in `models/schedule_model.py`.
*   **Fix**: Updated the `get_all_curriculum_details` query to use the correct column `dhi.bolum_id`, aligning with the recent schema changes in the `Ders_Havuz_Iliskisi` table.

### 4. Scripts Directory Cleanup
The `scripts/` directory was audited and organized:
*   **Deleted**: `fix_missing_departments.py` (Obsolete, functionality replaced by seeders).
*   **Moved**: `migrate_ders_tipi.py` to `scripts/migration/`.
*   **Updated**: 
    *   `populate_teachers.py`: Fixed imports to run with the new database structure.
    *   `assign_teachers.py`: Corrected project root path calculation.
    *   `export_pool_relationships.py`: Fixed SQL query to use `bolum_id`.

## Verification Results

*   **Teacher Population**: Executed `populate_teachers.py`, successfully adding **103** new teachers to the database.
*   **Teacher Assignment**: Executed `assign_teachers.py`, successfully creating **1233** course-teacher assignments.
*   **Data Integrity**: Ran `export_pool_relationships.py` which generated a complete report of pool-course relationships without SQL errors.
*   **Application Stability**: Confirmed the main application launches successfully and the Curriculum View now correctly displays data.
*   **New Feature**: Added "⚙️ Otomatik Kurulum / Veri Yükle" button in the Faculty/Dept menu to easily run setup scripts (Seeder, Teachers, Assignments) from the UI.
*   **Bug Fix**: Fixed `no such column: om.description` error by adding migration 005.
*   **Bug Fix**: Fixed "Empty Schedule List" issue by ensuring "Setup" runs:
    *   `populate_students.py` (Courses, Semester, Students)
    *   `populate_rooms.py` (Classrooms - **CRITICAL: was missing**)
    *   `populate_teachers.py` (Teachers)
    *   `assign_teachers.py` (Assignments)
*   **Bug Fix**: Fixed `table Ders_Programi has no column named derslik_id` error by adding migration 006 (adds `derslik_id` and `ders_tipi`).
*   **Success**: Confirmed that the "Otomatik Kurulum" process now fully populates the database and "Otomatik Program Oluştur" successfully generates and saves a schedule (Optimal Solution) to the database.
