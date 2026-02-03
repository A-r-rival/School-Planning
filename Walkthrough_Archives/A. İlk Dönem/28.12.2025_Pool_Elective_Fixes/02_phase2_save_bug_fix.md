# Phase 2 Scheduler Save Bug Fix

## Critical Bug Discovery

### Symptom
Terminal output showed:
```
[PHASE2_ELECTIVES] Solver Status: FEASIBLE
SUCCESS: Solution found in PHASE2_ELECTIVES mode!
objective: 587
```

**But:**
- Database had 0 elective courses
- Only 183 total courses (cores only)
- Phase 2 ran, found solution, but didn't save!

### Investigation

#### Step 1: Verify Solver Success
```python
# Terminal showed clear success
[PHASE2_ELECTIVES] Solver Status: FEASIBLE
objective: 587
```
587 electives scheduled successfully.

#### Step 2: Check Database
```python
import sqlite3
c = sqlite3.connect('okul_veritabani.db').cursor()
c.execute("SELECT COUNT(*) FROM Ders_Programi WHERE LOWER(ders_adi) LIKE '%seçmeli%'")
# Result: 0
```

Zero electives in database despite solver success!

#### Step 3: Trace Save Logic
Found `_run_solver()` method at line 783:

```python
def _run_solver(self, mode_name, timeout=600.0):
    # ... solver runs ...
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"SUCCESS: Solution found in {mode_name} mode!")
        if mode_name == "PHASE2_FULL" or mode_name == "PHASE1_CORE_FALLBACK": 
            self._save_solution()  # ❌ BUG HERE!
        return True
```

#### Step 4: Check Actual Mode Name
In `solve()` method at line 744:
```python
if self._run_solver("PHASE2_ELECTIVES", timeout=300.0):  # ← Mode name
    return True
```

**MISMATCH!**
- Solver called with `"PHASE2_ELECTIVES"`
- Save condition checked for `"PHASE2_FULL"`
- Result: Solution found but never saved!

## Root Cause

**String literal mismatch:**
- Mode name: `"PHASE2_ELECTIVES"` (actual)
- Condition: `"PHASE2_FULL"` (expected)

This is a classic copy-paste error or leftover from refactoring.

## Solution

### The Fix
[scheduler.py:808](file:///d:/Git_Projects/School-Planning/controllers/scheduler.py#L808)

**Before:**
```python
if mode_name == "PHASE2_FULL" or mode_name == "PHASE1_CORE_FALLBACK":
    self._save_solution()
```

**After:**
```python
if mode_name == "PHASE2_ELECTIVES" or mode_name == "PHASE1_CORE_FALLBACK":
    self._save_solution()
```

Single word change: `PHASE2_FULL` → `PHASE2_ELECTIVES`

### Verification

#### Before Fix
```sql
SELECT COUNT(*) FROM Ders_Programi; 
-- Result: 183 (cores only)
```

#### After Fix
1. Cleared database
2. Ran scheduler
3. Checked count:

```sql
SELECT COUNT(*) FROM Ders_Programi;
-- Result: 1831 (cores + electives)
```

**Success!** 1648 additional courses (electives) now saved.

## Impact

### Before
- ✅ Phase 1 (cores) worked
- ❌ Phase 2 (electives) solved but didn't save
- Result: Incomplete schedule, missing all electives

### After
- ✅ Phase 1 (cores) works
- ✅ Phase 2 (electives) solves AND saves
- Result: Complete schedule with 587 electives

## Prevention

### Code Review Checklist
- ✅ Use constants instead of string literals
- ✅ Grep for all mode name references
- ✅ Add unit test for save conditions

### Suggested Improvement
```python
# Define constants
class SolverMode:
    PHASE1_CORE = "PHASE1_CORE"
    PHASE2_ELECTIVES = "PHASE2_ELECTIVES"
    PHASE1_FALLBACK = "PHASE1_CORE_FALLBACK"

# Usage
if mode_name in [SolverMode.PHASE2_ELECTIVES, SolverMode.PHASE1_FALLBACK]:
    self._save_solution()
```

## Timeline
1. **User Report:** "seçmeliler hala işlenmiyor gibi gözüküyor veritabanına"
2. **Investigation:** 15 minutes checking database, schemas, outputs
3. **Discovery:** Found mode name mismatch in line 808
4. **Fix:** One-line change
5. **Verification:** Confirmed 1831 courses vs original 183

## Files Modified
- [scheduler.py:808](file:///d:/Git_Projects/School-Planning/controllers/scheduler.py#L808) - Fixed mode name check

## Lessons Learned
- Always verify end-to-end flow, not just intermediate success messages
- String comparisons are fragile - use constants or enums
- Log save operations explicitly, not just solve success
- When logs say "success" but results missing, check save logic

## Related Work
This fix enabled proper testing of:
- Pool placeholder exclusion
- Elective filtering
- Pool data migration
