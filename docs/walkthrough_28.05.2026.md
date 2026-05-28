# Walkthrough: ÜSD Standardization & Regex Centralization (28.05.2026)

## 1. ÜSD (Üniversite Seçmeli Dersler) Pool Standardization
- **Problem**: The raw file `Üniversites Seçmeli Dersler (ÜSD).txt` in the `database/Curriculum/` folder had inconsistent table structures (lacking standard T/U/L columns) and its header `[ÜSD] ÜNİVERSİTE SEÇMELİ DERSLER HAVUZU` was not recognized by the legacy parser.
- **Solution**: 
  - The raw file was meticulously reformatted to conform strictly to the `Curriculum_Reformatted` standard table design (`KOD | DERS ADI | ÖN KOS | DİL | T | U | L | AKTS`).
  - Added the `ÜSD HAVUZU` string pattern to the sanitizer (`format_and_translate.py`).
  - Adjusted the ingestion script's directory crawler to recursively ingest **all** `.txt` files rather than being constrained to explicit faculty subfolders.
- **Result**: The university-wide elective pool is now successfully reformatted and ingested by the `parse_curriculum.py` script. It accurately outputs to `curriculum_data.py` under the dictionary key `"Üniversites Seçmeli Dersler (ÜSD)"`, maintaining identical data structuring as individual faculty pools.

## 2. SOLID Refactoring: Regex Centralization (`curriculum_rules.py`)
- **Problem**: Both `parse_curriculum.py` and `curriculum_helpers.py` were tightly coupled with hardcoded Regex patterns (e.g. `Regexes` class) and evaluation methods (e.g. `is_pool_code_pattern`). This violated the Single Responsibility Principle and made future additions of new module types (e.g., a new "GSD" pool) fragile, as changes had to be synchronized across multiple scripts.
- **Solution**:
  - Created a new, standalone central ruleset module at `scripts/curriculum_rules.py`.
  - Migrated the `Regexes` class (containing patterns for `semester_term`, `year`, `season`, `pool_header`, and `pool_code`) into the new module.
  - Migrated the `is_pool_code_pattern(code)` method into the new module to serve as the unified authority on whether a string represents a pool code (like `SDIa` or `ZSD`) or a distinct course.
  - Refactored `parse_curriculum.py` and `curriculum_helpers.py` to `import` these rules from the new module.
- **Result**: A more modular, cleaner, and decoupled parsing logic. If a new pool designation is added to the school's format in the future, only `curriculum_rules.py` needs to be updated.

## 3. Post-Refactor Validation
- The parser (`parse_curriculum.py`) was executed against the entire `Curriculum_Reformatted` directory.
- The execution yielded a `0` exit code, confirming that the new import structures successfully resolve from the root directory.
- `output_debugging.txt` verified `0` parsing errors across all 9 faculties + the ÜSD pool.
- The `curriculum_data.py` database mapping is fully intact and synced.

## 4. Architecture: ScheduleModel Domain Repositories Refactoring
- **Problem**: The `ScheduleModel` class had grown into a massive "God Object" (over 2000 lines), making it difficult to maintain, prone to merge conflicts, and violating the Single Responsibility Principle. All database logic for every domain was stuffed into this single class.
- **Solution**: 
  - Created a new `models/repositories/` directory structure.
  - Implemented specific domain repositories: `TeacherRepository`, `CourseRepository`, `RoomRepository`, `StudentRepository`, and `FacultyDepartmentRepository` extending a common `BaseRepository` to share database connection logic.
  - Extracted domain-specific database operations and queries from `ScheduleModel.py` into their respective repositories.
  - Refactored `ScheduleModel` to act as a **Facade**, delegating all data-access calls (e.g., `self.room_repo.get_all_classrooms()`) so that existing views and controllers don't break.
- **Result**: `ScheduleModel` is drastically cleaner. Future database operations for a specific domain will now be added directly to the relevant repository, preventing further bloating of the main model class and facilitating concurrent development by multiple agents.
