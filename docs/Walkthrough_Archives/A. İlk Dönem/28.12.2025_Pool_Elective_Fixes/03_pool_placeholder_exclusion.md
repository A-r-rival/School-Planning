# Pool Placeholder Exclusion from Scheduling

## Problem Discovery

### User Report
After Phase 2 fix, user checked course list and found:
```
[SDUx] Zorunlu Seçmeli - Uzmanlık A, B, C veya D
[USD000] Üniversite Seçmeli Ders Havuzu
```

**Issue:** These are **placeholder courses** from student curriculum, not actual schedulable courses!

### Root Cause
`populate_students.py` creates curriculum placeholders like:
- `SDUx` - Represents any SD pool course choice
- `USD000` - University elective pool
- `GSD000`, `ZSD000` - Generic pool markers

These exist in `Dersler` table for student curriculum tracking but should **never** be scheduled as actual courses.

## Investigation

### Database Check
```python
c.execute("""
    SELECT ders_adi FROM Ders_Programi 
    WHERE ders_adi LIKE '%Havuz%' 
       OR ders_adi LIKE '%Pool%'
       OR ders_adi LIKE '%Uzmanlık%'
""")
```

**Found:**
- Multiple "Havuz" courses scheduled
- "Uzmanlık A, B, C veya D" entries
- Code patterns: SDUx, USD000, GSD000

### Why This Happens
Scheduler's `_fetch_all_course_instances()` loads from `Dersler` table:
```python
SELECT ders_adi, ders_instance, ... FROM Dersler
```

Placeholders are valid `Dersler` entries (for student tracking), so they get scheduled!

## Solution: Exclusion Logic

### Approach
Add exclusion rules in `_fetch_all_course_instances()` to skip placeholders.

### Implementation
[scheduler.py:213-227](file:///d:/Git_Projects/School-Planning/controllers/scheduler.py#L213-L227)

```python
# Pool placeholder exclusions (SDUx, USD000, ZSD000, etc.)
# These are student curriculum placeholders, not actual schedulable courses
if any(x in name_lower for x in [
    "seçmeli ders havuzu", "elective pool", "elective course pool",
    "uzmanlık a, b, c", "specialization a, b, c"
]):
    continue

# Also check course codes for placeholders
i_code = item_data.get('code', '')  # Get code from item_data
if i_code:
    code_upper = i_code.upper()
    # SDUx, USD000, GSD000, ZSD000, etc. (ends with x or 000)
    if code_upper.endswith('X') or code_upper.endswith('000'):
        if any(code_upper.startswith(prefix) for prefix in ['SDU', 'USD', 'GSD', 'ZSD', 'SD', 'ÜSD']):
            continue
```

### Exclusion Patterns

**Name-based:**
- "Seçmeli Ders Havuzu"
- "Elective Pool"
- "Uzmanlık A, B, C"
- "Specialization A, B, C"

**Code-based:**
- Ends with `X`: SDUx, USDx
- Ends with `000`: USD000, GSD000, ZSD000
- Starts with pool prefix: SD, ÜSD, GSD, ZSD, USD, SDU

### Why Both Name and Code?
- **Name check:** Catches verbose placeholders like "Üniversite Seçmeli Ders Havuzu"
- **Code check:** Catches code-only entries like `SDUx` or `USD000`
- **Belt and suspenders:** Redundancy ensures no placeholders slip through

## Verification

### Before Exclusion
```sql
SELECT COUNT(*) FROM Ders_Programi WHERE ders_adi LIKE '%Havuz%';
-- Result: 6+
```

### After Exclusion
```sql
SELECT COUNT(*) FROM Ders_Programi WHERE ders_adi LIKE '%Havuz%';
-- Result: 0
```

✅ No placeholders scheduled!

### Sample of Real Courses Now Scheduled
Instead of placeholders, actual elective courses scheduled:
- Yapay Zeka
- Veri Madenciliği
- Makine Öğrenmesi
- Bilgisayar Ağları
- etc.

## Edge Cases Handled

### 1. Code-only placeholders
Some entries have just code, no descriptive name:
```
Code: SDUx
Name: ""
```
→ Caught by code check

### 2. Descriptive placeholders
Some have full names:
```
Code: USD000
Name: "Üniversite Seçmeli Ders Havuzu / University Elective Pool"
```
→ Caught by name check

### 3. Pool-prefixed regular courses
**False positive risk:** Course named "Proje Yönetimi" with code "SD123"?

**Handled:** Code check requires:
- Ends with 'X' **OR** '000'
- "SD123" doesn't end with X or 000 → NOT excluded ✅

## Testing

### Test Matrix
| Course Code | Course Name | Excluded? | Reason |
|-------------|-------------|-----------|---------|
| SDUx | Zorunlu Seçmeli - Uzmanlık | ✅ Yes | Code ends with X |
| USD000 | Üniversite Seçmeli Havuzu | ✅ Yes | Code ends with 000 |
| GSD000 | Genel Seçmeli Havuzu | ✅ Yes | Code ends with 000 |
| ZSD123 | Yapay Zeka | ❌ No | Code doesn't end with X/000 |
| PRJ101 | Proje Yönetimi | ❌ No | Not a pool code |

## Impact

### Schedule Quality
- Before: Included unusable placeholder entries
- After: Only real, teachable courses scheduled

### Student Course Selection
- Placeholders remain in student curriculum (correct)
- Students select actual courses from pools
- Scheduler only schedules selected actual courses

## Files Modified
- [scheduler.py:213-227](file:///d:/Git_Projects/School-Planning/controllers/scheduler.py#L213-L227) - Exclusion logic

## Related Work
- Builds on existing project exclusion logic (lines 229-238)
- Complements pool data foundation (ensures only real courses in pools)

## Lessons Learned
- Scheduler data source != Display data source
- Curriculum tracking needs (placeholders) ≠ Scheduling needs (real courses)
- Multiple exclusion methods (name + code) provide robustness
- Always verify end-to-end: curriculum → scheduler → database → display
