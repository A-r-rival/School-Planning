# Implementation Plan: Cleanup, Fixes, and Modularization

The codebase has accumulated technical debt during feature development. This plan tracks completed fixes and outlines remaining refactoring work.

---

## ✅ Completed

### 1. Semester System Overhaul
Descriptive semester keys, Bahar course data population, all consumers updated.

| Dosya | Değişiklik |
|---|---|
| [parse_curriculum.py](file:///d:/Git_Projects/School-Planning/scripts/parse_curriculum.py) | `semester_key()` helper, descriptive keys |
| [populate_students.py](file:///d:/Git_Projects/School-Planning/scripts/populate_students.py) | String key parsing, `current_semester = year*2`, `Ders_Sinif_Iliskisi` for all semesters |
| [schedule_model.py](file:///d:/Git_Projects/School-Planning/models/schedule_model.py) | `_build_semester_lookup` updated for new keys |
| [calendar_view.py](file:///d:/Git_Projects/School-Planning/views/calendar_view.py) | Semester key lookup fixed for pool/staj/proje display |
| [curriculum_view.py](file:///d:/Git_Projects/School-Planning/views/curriculum_view.py) | Tuple index fix (`c[10]`/`c[11]` for IsPool/PoolCode) |

### 2. Scheduler Semester Filter
Replaced 70-line no-op filter in scheduler with actual `semester_lookup`-based filtering.

| Dosya | Değişiklik |
|---|---|
| [scheduler.py](file:///d:/Git_Projects/School-Planning/controllers/scheduler.py) | Real Güz/Bahar filter using `semester_lookup` |
| [schedule_view.py](file:///d:/Git_Projects/School-Planning/views/schedule_view.py) | Button renamed for clarity |

### 3. Module Renaming
`seeder.py` → `faculty_and_department_id_seeder.py`, all imports updated.

### 4. Previous Bug Fixes
- `TypeError` in `_run_scheduler` — fixed return type handling
- `KeyError: 'end_min'` — fixed time slot definitions
- Curriculum view tuple crash — fixed index mapping
- Phase 2 key mismatch warnings — fixed stable key generation
- Fixed room constraints enforced in Phase 1 & 2

---

## 🔲 Remaining Work

### ~~5. Duplicate & Obsolete Code Audit~~ ✅

Completed 16.02.2026. See [POST_AUDIT_REPORT](file:///d:/Git_Projects/School-Planning/docs/POST_AUDIT_REPORT%20%2816.02.26%29.md).
- 15 dead functions, 1 dead signal, 3 stale files deleted, 2 archived
- ~500 lines removed across 4 files
- FUTURE-marked: `export_schedule`, `import_schedule`

---

### ~~6. Project Structure Cleanup~~ ✅
Moved 13 loose debug/utility scripts from root to `scripts/debug/`.

- `debug_molbio.py`, `debug_teachers.py`
- `check_pool.py`, `check_rooms.py`
- `verify_fix_db.py`, `verify_parsing.py`
- `dump_lines_sem5.py`, `dump_lines_year3.py`, `dump_sem6.py`
- `find_lines_year3.py`
- `inspect_db.py`, `inspect_year3_pools.py`
- `report_bad_courses.py`

---

### 6.5 Bug: Ad-Hoc Courses Missing from Teacher Calendar

> [!WARNING]
> Ad-hoc courses added via "Bu Dönemlik Ekle" don't appear in the teacher calendar.

**Root cause:** `get_schedule_by_teacher()` uses `JOIN Dersler d ON ...` — if the ad-hoc course has no matching entry in `Dersler` (curriculum table), the JOIN drops it.

**Fix:** Change `JOIN` → `LEFT JOIN` in `get_schedule_by_teacher()`, or have the ad-hoc flow auto-create a minimal `Dersler` entry.

---

### 7. ScheduleModel Refactoring
Break down `ScheduleModel` (83KB monolith) by delegating to repositories.

#### [NEW] [classroom_repo.py](file:///d:/Git_Projects/School-Planning/models/repositories/classroom_repo.py)
- Create `ClassroomRepository`, move `get_all_classrooms_with_ids` and related logic.

#### [MODIFY] [teacher_repo.py](file:///d:/Git_Projects/School-Planning/models/repositories/teacher_repo.py)
- Move `get_teachers`, `get_all_teachers_with_ids` if not already present.

#### [MODIFY] [schedule_repo.py](file:///d:/Git_Projects/School-Planning/models/repositories/schedule_repo.py)
- Move `get_all_schedule_items` query logic.

#### [MODIFY] [schedule_model.py](file:///d:/Git_Projects/School-Planning/models/schedule_model.py)
- Remove raw SQL, inject repositories, delegate calls.

---

### 8. Scheduler Soft Constraints (Currently Disabled)
Two soft constraints were disabled during debugging and left as no-ops:

| Constraint | Location | Status |
|---|---|---|
| `add_soft_constraints_consecutive` | `scheduler.py:995` | Commented out, prints SKIPPED |
| `Teacher Day Span Optimization` | `scheduler.py:472` | Only prints SKIPPED, no implementation |

**Decision needed:** Re-enable consecutive constraints? Implement teacher day span?

---

## Verification Plan

### Automated
- Run `main.py` — verify startup without errors
- Trigger "Otomatik Kurulum / Veri Yükle" — verify Güz + Bahar data populated
- Run scheduler with Bahar filter — verify reduced course count and successful solve

### Manual
1. **Curriculum View**: Select Güz → zorunlu dersler visible. Select Bahar → zorunlu dersler visible.
2. **Calendar View**: Select Öğrenci Grubu → havuz/staj/proje labels appear top-right.
3. **Scheduler**: Select Bahar → run → verify ~250 courses (not 500).
