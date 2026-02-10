# Phase 5 Walkthrough: Course Repository

**Date**: 30.12.2024  
**Commits**: Multiple refinements  
**Status**: ✅ Complete

---

## Objective
Extract course-related SQL operations into a dedicated repository with type-safe DTOs and clean architectural boundaries.

---

## Created Files

### CourseRepository (120 lines)
**Location**: `models/repositories/course_repo.py`

**Key Features**:
- NamedTuple DTOs for type safety
- No transaction management (cursor-only)
- `_execute()` wrapper for future extensibility
- Clean `get_or_create` API with exists flag

---

## Evolution: Three Iterations

### Iteration 1: Basic Repository
```python
def get_or_create(self, name: str, code: str = "CODE") -> Tuple[int, str]:
    # Returns (instance, code)
    # Problem: Caller doesn't know if course exists
```

### Iteration 2: Added Exists Flag
```python
def get_or_create(self, name: str, code: str = "CODE") -> Tuple[int, str, bool]:
    # Returns (instance, code, exists)
    # Better, but magic tuple is unclear
```

### Iteration 3: NamedTuple (Final) ✅
```python
class CourseLookupResult(NamedTuple):
    instance: int
    code: str
    exists: bool  # False = caller must create

def get_or_create(self, name: str, code: str = "CODE") -> CourseLookupResult:
    return CourseLookupResult(instance, code, exists=True)
```

**Usage**:
```python
result = repo.get_or_create("Matematik", "MAT101")
if not result.exists:  # Named field - crystal clear!
    instance = model.ders_ekle(name, result.code, ...)
```

---

## Key Design Decisions

### 1. Removed `conn` Parameter

**Before**:
```python
def __init__(self, cursor: sqlite3.Cursor, conn: sqlite3.Connection):
    self._cursor = cursor
    self._conn = conn  # Never used!
```

**After**:
```python
def __init__(self, cursor: sqlite3.Cursor):
    self._cursor = cursor
```

**Rationale**:
- Repository doesn't commit
- Transactions managed by caller
- Clearer separation of concerns
- Consistent with "repository doesn't manage transactions" principle

---

### 2. NamedTuple DTOs

**Created Two DTOs**:

```python
class CourseInstance(NamedTuple):
    """Represents a course instance (section)."""
    instance: int
    code: str

class CourseLookupResult(NamedTuple):
    """Result of get_or_create lookup."""
    instance: int
    code: str
    exists: bool
```

**Benefits**:
- ✅ Type-safe returns
- ✅ Named fields (no tuple[0] confusion)
- ✅ IDE autocomplete
- ✅ Self-documenting code

**Before**:
```python
instance, code, exists = repo.get_or_create(...)
# What does index 2 mean again?
```

**After**:
```python
result = repo.get_or_create(...)
if not result.exists:  # Clear!
    print(f"Need to create {result.code}")
```

---

### 3. `_execute()` Wrapper

**Implementation**:
```python
def _execute(self, sql: str, params: tuple = ()):
    """
    Single point for SQL execution.
    Future: add logging, timing, debug here.
    """
    self._cursor.execute(sql, params)
    return self._cursor
```

**Usage**:
```python
def exists(self, name: str) -> bool:
    return self._execute(
        "SELECT 1 FROM Dersler WHERE ders_adi = ? LIMIT 1",
        (name,)
    ).fetchone() is not None
```

**Future Extensions** (without changing repo code):
```python
def _execute(self, sql: str, params: tuple = ()):
    start = time.time()
    logger.debug(f"SQL: {sql} | Params: {params}")
    
    self._cursor.execute(sql, params)
    
    duration = time.time() - start
    if duration > 0.1:
        logger.warning(f"Slow query: {sql} took {duration}s")
    
    return self._cursor
```

---

## Repository Methods

```python
class CourseRepository:
    def get_or_create(name, default_code) -> CourseLookupResult
    def get_all() -> List[tuple[str, str]]
    def exists(name) -> bool
    def get_by_name(name) -> Optional[tuple[int, str, str]]
    def get_instances(name) -> List[CourseInstance]
```

**Total**: 5 public methods, 2 helpers

---

## Integration with schedule_model.py

### Refactored add_course

**Before (17 lines of inline SQL)**:
```python
# 2. Ensure Course exists
self.c.execute("SELECT ders_instance, ders_kodu FROM Dersler WHERE ders_adi = ?", (ders_adi,))
course_rows = self.c.fetchall()

if not course_rows:
    default_code = "CODE"
    instance = self.ders_ekle(ders_adi, ders_kodu=default_code, ...)
    current_code = default_code
else:
    instance = course_rows[0][0]
    current_code = course_rows[0][1] if course_rows[0][1] else "CODE"
```

**After (4 lines with repository)**:
```python
# 2. Get or create course using repository
result = self.course_repo.get_or_create(ders_adi, "CODE")

if not result.exists:
    instance = self.ders_ekle(ders_adi, ders_kodu=result.code, ...)
```

**Reduction**: 17 lines → 4 lines (76% reduction)

---

## Code Comparison: Type Safety

### Magic Tuples (Before)
```python
# What does each position mean?
row = cursor.fetchone()
if row:
    id = row[0]      # ders_id? instance?
    name = row[1]    # ders_adi?
    code = row[2]    # ders_kodu?
```

### Named Types (After)
```python
result = repo.get_or_create("Matematik")
print(result.instance)  # Autocomplete!
print(result.code)      # Clear!
print(result.exists)    # Self-documenting!
```

---

## Code Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Course SQL in model** | 17 lines | 4 lines | -76% |
| **Type safety** | Tuple[int, str, bool] | NamedTuple | ✅ |
| **Repository methods** | 0 | 5 | ✅ |
| **_execute wrapper** | No | Yes | Future-proof |
| **Transaction coupling** | conn needed | cursor only | Decoupled |

---

## Production-Grade Features

### 1. Transaction Independence
```python
# Repository doesn't know about commits
repo = CourseRepository(cursor)  # No conn!

# Service/Model manages transactions
with conn:
    result = repo.get_or_create(...)
    if not result.exists:
        model.ders_ekle(...)
    # Commit here
```

### 2. Type-Safe Returns
```python
# IDE knows these fields exist
result: CourseLookupResult = repo.get_or_create(...)
result.instance  # ✅ Type-checked
result.exists    # ✅ Boolean
```

### 3. Consistent Ordering
```python
def _fetch_instances(self, name: str):
    return self._execute(
        "... ORDER BY ders_instance",  # Always sorted
        (name,)
    ).fetchall()
```

### 4. Extensibility Hook
```python
def _execute(self, sql: str, params: tuple = ()):
    # Single point for:
    # - Logging
    # - Metrics
    # - Query caching
    # - Debug tracing
    self._cursor.execute(sql, params)
    return self._cursor
```

---

## Testing Strategy (Future)

With this design, testing is trivial:

```python
def test_get_or_create_existing():
    cursor = Mock()
    cursor.fetchall.return_value = [(1, "MAT101")]
    
    repo = CourseRepository(cursor)
    result = repo.get_or_create("Matematik")
    
    assert result.exists == True
    assert result.instance == 1
    assert result.code == "MAT101"

def test_get_or_create_new():
    cursor = Mock()
    cursor.fetchall.return_value = []
    
    repo = CourseRepository(cursor)
    result = repo.get_or_create("Fizik", "FIZ101")
    
    assert result.exists == False
    assert result.code == "FIZ101"
```

---

## Files Modified

- `models/repositories/course_repo.py` - New (+120 lines)
- `models/repositories/__init__.py` - Export CourseRepository (+1 line)
- `models/schedule_model.py` - Integration
  - `__init__`: Initialize repo (+1 line)
  - `add_course`: Use repo.get_or_create (-13 lines)

**Net Impact**: +120 lines (new repository), -13 lines (inline SQL removed)

---

## Benefits Summary

1. **Type Safety**: NamedTuple DTOs eliminate magic tuples
2. **Clear API**: `result.exists` is self-documenting
3. **Decoupled**: No transaction management in repo
4. **Extensible**: `_execute()` hook for future features
5. **Testable**: Easy to mock, no DB needed
6. **DRY**: `_fetch_instances()` helper

---

## Lessons Learned

### Don't: Magic Tuples
```python
❌ Tuple[int, str, bool]  # What's bool?
```

### Do: Named Types
```python
✅ CourseLookupResult(instance, code, exists)
```

### Don't: Repository Commits
```python
❌ repo.__init__(cursor, conn)  # Why conn?
```

### Do: Caller Controls Transactions
```python
✅ repo.__init__(cursor)  # Clean boundary
```

---

## Next Phase
Phase 6: Extract ScheduleFormatter to separate UI string formatting from model logic.
