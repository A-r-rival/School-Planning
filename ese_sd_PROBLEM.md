# Investigation: Energy Systems Engineering (ESE) Elective Problem

## Problem Description
Energy Systems Engineering (Enerji Bilimleri) 3rd and 4th year electives are appearing in the calendar as scheduled mandatory courses, while other departments' electives are not. The expected behavior is that these should be selectable/pool courses, not mandatory scheduled blocks.

## Findings

1.  **Courses Identified:**
    - The courses causing the issue are primarily:
        - `ISG001` (İş Sağlığı ve Güvenliği)
        - `ÜSDI` (Üniversite Seçmeli Ders)
        - `SDII` (Seçmeli Ders II)
    - These are explicitly listed in the **Energy Systems Curriculum** text file (Semesters 7 and 8) as distinct entries rows.

2.  **Root Cause:**
    - **Treated as Core Courses:** because these courses are explicitly listed in the semester plan (parsed into `Ders_Sinif_Iliskisi`), the system treats them as **Core/Mandatory** courses for that class year.
    - **Regex/Filter Mismatch:** 
        - `ISG001` does not match the standard "Pool Code" regex used to separate electives (e.g., it doesn't contain "SD" in a way that triggers the pool logic).
        - `SD` and `ÜSD` *are* pool codes, but because they are also listed as direct rows in the curriculum file (not just in the pool definition section), they get added to the `Ders_Sinif_Iliskisi` table as normal courses.
    - **Auto-Scheduling:** The "Generate Schedule" algorithm schedules all mandatory courses found in `Ders_Sinif_Iliskisi`. Since the system sees these as mandatory for the class, it assigns them slots.

3.  **Why Others Are Different:**
    - Other departments either don't have these specific codes listed as main courses, or their specific elective codes (like `SDIa`) are correctly caught by the pool regex and excluded from the mandatory course list during scheduling.

## Technical Details
- **Database Table:** `Ders_Sinif_Iliskisi` contains entries for these courses linked to Dept ID 101 (Energy Systems).
- **Curriculum File:** `database/Curriculum/Fen Fakültesi/Enerji Bilimi ve Teknolojileri Öğretim Planı.txt`
- **Logic:** `ScheduleService` -> `generate_schedule` -> fetches all courses for the semester. It doesn't distinguish these "placeholder" names from real courses if they are in the main list.

## Recommendation / Fix
To fix this, we need to:
1.  **Metadata Update:** Ensure these courses are marked as `is_elective=True` or `is_pool=True` in the database, even if they are in the main list.
2.  **Parser Update:** Modify `parse_curriculum.py` to treat `ISG001`, `ÜSD*`, and `SD*` as pool placeholders even if they appear in the semester table, preventing them from being added as standard mandatory courses.
3.  **Immediate Workaround:** Manually remove these course entries from the `Ders_Programi` (Scheduled) table or `Ders_Sinif_Iliskisi` (Curriculum) table.
