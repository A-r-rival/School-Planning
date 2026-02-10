# Database Migration - Pool Relationships

## Overview
Populated `Ders_Havuz_Iliskisi` table with pool-course relationships extracted from curriculum_data.py.

## Prerequisites
1. ✅ `Ders_Havuz_Iliskisi` table created ([schedule_model.py:94-103](file:///d:/Git_Projects/School-Planning/models/schedule_model.py#L94-L103))
2. ✅ `curriculum_data.py` has `pool_codes` populated (see [04_parse_curriculum_pools.md](04_parse_curriculum_pools.md))

## Migration Script

### Purpose
Read pool relationships from curriculum_data.py and insert into database table.

### Implementation
[migrate_pool_relationships.py](file:///d:/Git_Projects/School-Planning/debugs/29.12.2024_Pool_Elective_Session/migrate_pool_relationships.py)

```python
from scripts.curriculum_data import DEPARTMENTS_DATA

# Get department IDs
c.execute("SELECT bolum_num, bolum_adi FROM Bolumler")
dept_map = {name: num for num, name in c.fetchall()}

for dept_name, dept_data in DEPARTMENTS_DATA.items():
    bolum_num = dept_map[dept_name]
    pool_codes = dept_data.get('pool_codes', {})
    
    for havuz_kodu, courses in pool_codes.items():
        for course_name in courses:
            # Find course in Dersler table
            c.execute("SELECT ders_instance FROM Dersler WHERE ders_adi = ? LIMIT 1", 
                     (course_name,))
            
            result = c.fetchone()
            if result:
                ders_instance = result[0]
                c.execute("""
                    INSERT INTO Ders_Havuz_Iliskisi 
                    (ders_instance, ders_adi, bolum_num, havuz_kodu)
                    VALUES (?, ?, ?, ?)
                """, (ders_instance, course_name, bolum_num, havuz_kodu))
```

## Execution

```bash
python migrate_pool_relationships.py
```

**Output:**
```
Cleared existing pool relationships

✅ Migration Complete!
   Inserted: 668 pool relationships
   Skipped: X (duplicates or missing courses)

Sample pool relationships:
  Yapay Zeka | Bilgisayar Müh | ZSD
  Veri Madenciliği | Bilgisayar Müh | ZSD
  ...
```

## Results

### Table Statistics
```sql
SELECT COUNT(*) FROM Ders_Havuz_Iliskisi;
-- 668 relationships

SELECT COUNT(DISTINCT bolum_num) FROM Ders_Havuz_Iliskisi;
-- 15 departments

SELECT COUNT(DISTINCT havuz_kodu) FROM Ders_Havuz_Iliskisi;
-- 51 pools
```

### Top Pools
```sql
SELECT havuz_kodu, COUNT(*) 
FROM Ders_Havuz_Iliskisi 
GROUP BY havuz_kodu 
ORDER BY COUNT(*) DESC 
LIMIT 10;
```

| Pool Code | Courses |
|-----------|---------|
| ZSD | 95 |
| SDVIII | 56 |
| SDVII | 56 |
| SDVI | 56 |
| SDV | 56 |
| SDIII | 52 |
| ÜSD | 40 |
| SDIa | 34 |
| SDIb | 29 |
| POLSDV | 26 |

### Sample Relationships
```sql
SELECT B.bolum_adi, D.havuz_kodu, D.ders_adi
FROM Ders_Havuz_Iliskisi D
JOIN Bolumler B ON D.bolum_num = B.bolum_num
WHERE D.havuz_kodu = 'ZSD'
LIMIT 5;
```

| Department | Pool | Course |
|------------|------|--------|
| Bilgisayar Müh | ZSD | Yapay Zeka |
| Bilgisayar Müh | ZSD | Veri Madenciliği |
| Bilgisayar Müh | ZSD | Makine Öğrenmesi |
| Elektrik-Elektronik Müh | ZSD | Güç Elektroniği |
| ... | ... | ... |

## Verification

### Export to Text File
Created utility script to export relationships:
```bash
python scripts/export_pool_relationships.py
```

**Output:** `pool_course_relationships.txt` (moved to debugs folder)

**Format:**
```
================================================================================
Bilgisayar Müh
================================================================================

  [ZSD] - 12 ders
  ----------------------------------------------------------------------------
    • Yapay Zeka
    • Veri Madenciliği
    • Makine Öğrenmesi
    ...
```

## Schema Details

### Ders_Havuz_Iliskisi Table
```sql
CREATE TABLE IF NOT EXISTS Ders_Havuz_Iliskisi (
    iliski_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ders_instance INTEGER NOT NULL,
    ders_adi TEXT NOT NULL,
    bolum_num INTEGER NOT NULL,  -- Which department sees this pool
    havuz_kodu TEXT NOT NULL,    -- Pool code: ZSD, ÜSD, GSD, etc.
    
    FOREIGN KEY (ders_instance, ders_adi) REFERENCES Dersler(...),
    FOREIGN KEY (bolum_num) REFERENCES Bolumler(bolum_num),
    
    UNIQUE(ders_instance, ders_adi, bolum_num, havuz_kodu)
);
```

### Key Features
- **Composite Primary Key:** (ders_instance, ders_adi, bolum_num, havuz_kodu)
- **Foreign Keys:** Maintain referential integrity
- **UNIQUE Constraint:** Prevents duplicate relationships

## Future Applications

### 1. Pool-Based Filtering
```sql
-- Get all ZSD courses for a department
SELECT ders_adi FROM Ders_Havuz_Iliskisi
WHERE bolum_num = 111 AND havuz_kodu = 'ZSD';
```

### 2. Cross-Department Electives
```sql
-- Find courses offered as different pools in different depts
SELECT ders_adi, COUNT(DISTINCT havuz_kodu) as pool_count
FROM Ders_Havuz_Iliskisi
GROUP BY ders_adi
HAVING pool_count > 1;
```

### 3. Pool Capacity Planning
```sql
-- How many courses per pool per department?
SELECT B.bolum_adi, D.havuz_kodu, COUNT(*) as course_count
FROM Ders_Havuz_Iliskisi D
JOIN Bolumler B ON D.bolum_num = B.bolum_num
GROUP BY B.bolum_adi, D.havuz_kodu
ORDER BY B.bolum_adi, course_count DESC;
```

## Files
- **Migration Script:** [migrate_pool_relationships.py](file:///d:/Git_Projects/School-Planning/debugs/29.12.2024_Pool_Elective_Session/migrate_pool_relationships.py)
- **Export Utility:** [scripts/export_pool_relationships.py](file:///d:/Git_Projects/School-Planning/scripts/export_pool_relationships.py)
- **Schema Definition:** [schedule_model.py:94-103](file:///d:/Git_Projects/School-Planning/models/schedule_model.py#L94-L103)

## Impact
✅ Database-driven pool filtering now possible
✅ Foundation for future pool-based features
✅ Cross-department elective tracking enabled
✅ Scheduler can use pool data for soft constraints

## Related Work
- Prerequisites: [04_parse_curriculum_pools.md](04_parse_curriculum_pools.md)
- Enabled: Radio button filter functionality
- Future: Calendar pool checkboxes, scheduler pool penalties
