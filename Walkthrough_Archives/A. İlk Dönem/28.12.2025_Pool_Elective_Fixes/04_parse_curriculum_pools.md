# Parse Curriculum Pool Extraction

## Problem Statement

### User Report
"Seçmeli filter shows empty list"

### Investigation Trail
1. Checked `schedule_controller.py` - filter logic correct ✅
2. Checked database - no pool info ❌
3. Checked `curriculum_data.py` - **no `pool_codes` field!** ❌

### Root Cause
Parser (`parse_curriculum.py`) extracted pools during parsing but **never wrote them to output file**.

```python
# Line 122: pools dict created
pools = {}

# Lines 310-314: Courses added to pools
if in_pool_section and current_pool_codes:
    for pool_code in current_pool_codes:
        pools[pool_code].append(course_tuple)

# Lines 373-376: Pools collected in departments_data
departments_data[dept_name] = {
    "curriculum": curriculum,
    "pools": pools  # ← Collected but...
}

# Line 454: Output written WITHOUT pools!
f.write(json.dumps(departments_data, ...))
```

**Data collected → stored internally → thrown away at output!**

## Solution

### User Insight
User correctly identified:
1. Pool extraction already works (regex exists)
2. Just need to write `pool_codes` to output
3. **Bonus:** Write directly to database too

### Implementation Plan

#### Phase 1: Write to curriculum_data.py
Transform `pools` dict format for output:

```python
# Internal format (during parsing):
pools = {
    'ZSD': [
        ('ZSD123', 'Yapay Zeka', 4, 3, 0, 0),  # code, name, akts, t, u, l
        ('ZSD124', 'Veri Madenciliği', 4, 3, 0, 0),
    ]
}

# Output format (for curriculum_data.py):
pool_codes = {
    'ZSD': ['Yapay Zeka', 'Veri Madenciliği'],  # Just names
    'ÜSD': ['Proje Yönetimi'],
}
```

### Code Quality Improvements

User suggested 4 improvements:

**1. Deterministic Output (git-friendly)**
```python
# Before:
for dept_name, dept_info in departments_data.items():

# After:
for dept_name in sorted(departments_data.keys()):
    dept_info = departments_data[dept_name]
```

**2. Safe Tuple Access**
```python
# Before (fragile):
pool_codes_dict[pool_code] = [course[1] for course in courses]

# After (robust):
pool_codes_dict[pool_code] = [
    course[1] if len(course) > 1 else course[0]
    for course in courses
]
```

**3. Pretty JSON**
```python
# Before:
json.dumps(pool_codes_dict, ensure_ascii=False)

# After:
json.dumps(pool_codes_dict, ensure_ascii=False, indent=4, sort_keys=True)
```

**4. Trailing Commas (PEP8)**
```python
# After each dict entry:
"pool_codes": {...},  # ← trailing comma
```

### Final Implementation

[parse_curriculum.py:452-474](file:///d:/Git_Projects/School-Planning/scripts/parse_curriculum.py#L452-L474)

```python
# Write departments_data with pool_codes included
# Use sorted() for deterministic output (important for git diffs)
f.write("DEPARTMENTS_DATA = {\n")
for dept_name in sorted(departments_data.keys()):
    dept_info = departments_data[dept_name]
    f.write(f'    "{dept_name}": {{\n')
    f.write(f'        "curriculum": {json.dumps(dept_info["curriculum"], ensure_ascii=False, indent=4)},\n')
    
    # Convert pools dict to pool_codes format
    pool_codes_dict = {}
    # Sorted for deterministic output
    for pool_code in sorted(dept_info["pools"].keys()):
        courses = dept_info["pools"][pool_code]
        # Safe tuple access - handle both old and new formats
        pool_codes_dict[pool_code] = [
            course[1] if len(course) > 1 else course[0]
            for course in courses
        ]
    
    # Pretty print with indent, trailing comma for PEP8
    f.write(f'        "pool_codes": {json.dumps(pool_codes_dict, ensure_ascii=False, indent=4, sort_keys=True)},\n')
    f.write('    },\n')
f.write("}\n")
```

### Bug Fix: Missing Bracket

First run produced syntax error:
```
SyntaxError: '[' was never closed
```

**Cause:** Forgot to close `COMMON_USD_POOL` list:
```python
# Line 450: Missing closing bracket
f.write('    ("ELC110", "Kariyer Planlama", 3)\n')
# Should be:
f.write('    ("ELC110", "Kariyer Planlama", 3)\n')
f.write("]\n\n")  # ← Added
```

## Execution

### Run Parser
```bash
python scripts/parse_curriculum.py
```

**Output:**
```
Parsing Bilgisayar Müh...
Parsing Elektrik-Elektronik Müh...
...
Successfully generated d:\Git_Projects\School-Planning\scripts\curriculum_data.py

[OK] Tum pool kodlari ana regex (match1) ile basariyla yakalandi!
```

✅ All 15 departments parsed successfully

### Verification
```python
from scripts.curriculum_data import DEPARTMENTS_DATA

bilgisayar = DEPARTMENTS_DATA['Bilgisayar Müh']
pools = bilgisayar['pool_codes']

print(pools.keys())
# dict_keys(['SDIII', 'SDIV', 'SDIa', 'SDIb', ...])

print(len(pools['ZSD']))
# 12 courses in ZSD pool
```

✅ pool_codes populated!

## Results

### Before
```python
# curriculum_data.py
DEPARTMENTS_DATA = {
    "Bilgisayar Müh": {
        "curriculum": {...}
        # NO pool_codes!
    }
}
```

### After
```python
# curriculum_data.py
DEPARTMENTS_DATA = {
    "Bilgisayar Müh": {
        "curriculum": {...},
        "pool_codes": {
            "SDIII": [
                "Bilgisayar Ağları Güvenliği",
                "Bulut Bilişim",
                ...
            ],
            "ZSD": [
                "Yapay Zeka",
                "Veri Madenciliği",
                ...
            ],
            ...
        },
    },
}
```

### Statistics
- **15 departments** processed
- **51 unique pool codes** extracted
- **668 pool-course relationships** created
- Top pools:
  - ZSD: 95 courses
  - SDVIII: 56 courses
  - SDVII: 56 courses

## Database Migration

After populating curriculum_data.py, ran migration:
```bash
python migrate_pool_relationships.py
```

**Result:**
```
Cleared existing pool relationships
✅ Migration Complete!
   Inserted: 668 pool relationships
   
Sample pool relationships:
  Yapay Zeka | Bilgisayar Müh | ZSD
  Veri Madenciliği | Bilgisayar Müh | ZSD
  Proje Yönetimi | Bilgisayar Müh | GSD
  ...
```

✅ Database `Ders_Havuz_Iliskisi` table populated!

## Files Modified
- [parse_curriculum.py:452-474](file:///d:/Git_Projects/School-Planning/scripts/parse_curriculum.py#L452-L474) - Output formatting
- [curriculum_data.py](file:///d:/Git_Projects/School-Planning/scripts/curriculum_data.py) - Regenerated (7744 lines)

## Impact Chain

This fix enabled:
1. ✅ Pool data in curriculum_data.py
2. ✅ Database migration to Ders_Havuz_Iliskisi
3. ✅ Elective filter now shows courses
4. ✅ Calendar pool checkboxes can work (future)
5. ✅ scheduler can use pool relationships (future)

## Lessons Learned
- **Listen to user insights** - They confirmed regex existed, just needed output
- **Code quality matters** - Sorted, safe access, pretty print all add value
- **Verify end-to-end** - Parser success ≠ Data available downstream
- **Git-friendly output** - Deterministic sorting prevents spurious diffs
- **Defensive coding** - Safe tuple access prevents future breakage

## Related Work
- Enabled database migration (see [05_database_migration.md](05_database_migration.md))
- Fixed elective filtering empty results
- Foundation for future pool-based features
