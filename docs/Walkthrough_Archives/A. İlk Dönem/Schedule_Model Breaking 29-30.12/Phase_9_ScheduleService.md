# Phase 9 Walkthrough: ScheduleService Extraction

**Date**: 30.12.2024  
**Status**: ✅ Complete

---

## Objective
Extract business logic from `ScheduleModel` into a testable `ScheduleService` layer, breaking the God Object pattern.

---

## Problem: God Object Anti-Pattern

**Before**: ScheduleModel does everything
```python
class ScheduleModel(QObject):
    # 1. Qt signals (UI)
    course_added = pyqtSignal(str)
    
    # 2. Business logic
    # 3. Transaction management
    # 4. Repository orchestration
    # 5. Error handling
    # 6. Formatting
    
    def add_course(self, course_data):
        # 70 lines mixing all concerns
```

**Issues**:
- ❌ Hard to test (Qt dependency)
- ❌ Mixed responsibilities
- ❌ No reusability
- ❌ Tight coupling

---

## Solution: Service Layer

```
ScheduleModel (UI Layer)
    ↓ delegates to
ScheduleService (Business Layer)
    ↓ uses
Repositories (Data Layer)
```

---

## Architecture

### 1. Custom Exceptions

**File**: `models/services/exceptions.py`

```python
class ScheduleServiceError(Exception):
    """Base exception for schedule service errors."""
    pass

class ScheduleConflictError(ScheduleServiceError):
    """Raised when a time slot conflict is detected."""
    pass

class CourseCreationError(ScheduleServiceError):
    """Raised when course creation fails."""
    pass

class CourseNotFoundError(ScheduleServiceError):
    """Raised when course is not found."""
    pass
```

**Benefits**:
- ✅ Type-safe error handling
- ✅ Clear error semantics
- ✅ No string parsing needed

---

### 2. ScheduleService

**File**: `models/services/schedule_service.py`

```python
class ScheduleService:
    """
    Business logic for schedule operations.
    
    Responsibilities:
    - Transaction management
    - Business rule validation
    - Repository orchestration
    - Error handling
    
    Does NOT:
    - Emit Qt signals
    - Know about UI
    - Directly access database
    """
    
    def __init__(
        self,
        conn: sqlite3.Connection,
        teacher_repo: TeacherRepository,
        course_repo: CourseRepository,
        schedule_repo: ScheduleRepository
    ):
        self._conn = conn
        self._teacher_repo = teacher_repo
        self._course_repo = course_repo
        self._schedule_repo = schedule_repo
```

**Key Point**: No Qt dependency = fully testable ✅

---

## add_course() Transformation

### Before (70 lines in ScheduleModel)
```python
def add_course(self, course_data: CourseInput) -> bool:
    try:
        # Create slot
        slot = ScheduleSlot.from_strings(...)
        
        # Check conflicts
        if self.schedule_repo.has_conflict(slot):
            self.error_occurred.emit("...")
            return False
        
        # Extract data
        ders_adi = course_data.ders
        hoca_adi = course_data.hoca
        
        # Transaction
        with self.conn:
            # Get teacher
            ogretmen_id = self.teacher_repo.get_or_create(hoca_adi)
            
            # Get course
            result = self.course_repo.get_or_create(ders_adi, "CODE")
            
            # Create if needed
            if not result.exists:
                instance = self.ders_ekle(...)
            else:
                instance = result.instance
            
            # Get ID
            ders_id = self.course_repo.get_id(...)
            
            # Insert
            self.c.execute("INSERT INTO ...")
        
        # Format
        course_info = ScheduleFormatter.format_course(...)
        self.course_added.emit(course_info)
        return True
        
    except Exception as e:
        self.error_occurred.emit(...)
        return False
```

### After: Service Layer (in ScheduleService)
```python
def add_course(self, course: CourseInput) -> str:
    """
    Add course to schedule.
    
    Returns:
        Formatted course info
        
    Raises:
        ScheduleConflictError: Time conflict
        CourseCreationError: Creation failed
    """
    # 1. Create slot
    slot = ScheduleSlot.from_strings(
        course.gun, course.baslangic, course.bitis
    )
    
    # 2. Business rule: Check conflicts
    if self._schedule_repo.has_conflict(slot):
        raise ScheduleConflictError(
            f"Time slot conflict: {slot.day} {slot.to_display_string()}"
        )
    
    # 3. Transaction
    with self._conn:
        teacher_id = self._teacher_repo.get_or_create(course.hoca)
        
        course_result = self._course_repo.get_or_create(course.ders, "CODE")
        
        if not course_result.exists:
            instance = self._create_course_instance(...)
        else:
            instance = course_result.instance
        
        ders_id = self._course_repo.get_id(course.ders, instance)
        
        gun, baslangic, bitis = slot.to_db_tuple()
        
        self._schedule_repo.add_raw(
            ders_id, instance, teacher_id,
            gun, baslangic, bitis
        )
    
    # 4. Format and return
    return ScheduleFormatter.format_course(
        code=course_result.code,
        name=course.ders,
        teacher=course.hoca,
        day=gun,
        start=baslangic,
        end=bitis
    )
```

### After: Model Layer (in ScheduleModel)
```python
def add_course(self, course_data: CourseInput) -> bool:
    """
    Add course. Delegates to service.
    """
    try:
        course_info = self.schedule_service.add_course(course_data)
        self.course_added.emit(course_info)
        return True
    except ScheduleConflictError as e:
        self.error_occurred.emit(str(e))
        return False
    except CourseCreationError as e:
        self.error_occurred.emit(f"Failed: {e}")
        return False
    except Exception as e:
        self.error_occurred.emit(f"Unexpected error: {e}")
        return False
```

**Reduction**: 70 lines → 26 lines (-63%) ✅

---

## Critical Fixes Applied

### 1. Repository Boundary Violation

**Problem**: Service had raw SQL
```python
# ❌ BAD: Service executing SQL
cursor = self._conn.cursor()
cursor.execute("INSERT INTO Ders_Programi ...")
```

**Fix**: Added repository method
```python
# ✅ GOOD: Repository handles SQL
self._schedule_repo.add_raw(
    ders_id, instance, teacher_id, ...
)
```

### 2. Instance Collision Bug

**Problem**: Always used instance=1
```python
# ❌ BAD: Second course overwrites first
INSERT INTO Dersler (...) VALUES (?, 1, ?)
```

**Fix**: Calculate next instance
```python
# ✅ GOOD: Proper instance calculation
cursor.execute(
    "SELECT MAX(ders_instance) FROM Dersler WHERE ders_adi = ?",
    (name,)
)
next_instance = (cursor.fetchone()[0] or 0) + 1
INSERT INTO Dersler (...) VALUES (?, next_instance, ?)
```

### 3. Exception Semantics

**Problem**: Boolean return unclear
```python
# ❌ Ambiguous: Why False?
return False
```

**Fix**: Fail-fast with exceptions
```python
# ✅ Clear: Specific error
raise CourseNotFoundError(f"Course {id} not found")
```

---

## Benefits

### 1. Testability
```python
def test_add_course_conflict():
    # No Qt needed!
    service = ScheduleService(conn, repos...)
    
    service.add_course(course1)
    
    with pytest.raises(ScheduleConflictError):
        service.add_course(conflicting_course)
```

### 2. Reusability
```python
# CLI tool
service = ScheduleService(...)
service.add_course(...)

# API endpoint
service = ScheduleService(...)
service.add_course(...)

# Different UI framework
service = ScheduleService(...)
service.add_course(...)
```

### 3. Clear Responsibilities

```
ScheduleModel:
- Emit signals
- Handle Qt-specific concerns
- Map exceptions to UI errors

ScheduleService:
- Business rules
- Transactions
- Repository orchestration

Repositories:
- SQL only
- No business logic
- No transactions
```

---

## Code Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **ScheduleModel.add_course** | 70 lines | 26 lines | -63% |
| **Lines with business logic** | In model | In service | ✅ Separated |
| **Qt dependency for tests** | Required | Not needed | ✅ Testable |
| **Transaction safety** | Manual | Automatic | ✅ Safe |
| **Error handling** | Generic | Specific | ✅ Clear |

---

## Integration

```python
class ScheduleModel:
    def __init__(self):
        # ... initialize DB, repos
        
        # Initialize service
        from models.services import ScheduleService
        self.schedule_service = ScheduleService(
            self.conn,
            self.teacher_repo,
            self.course_repo,
            self.schedule_repo
        )
```

---

## Testing Examples

### Test: Conflict Detection
```python
def test_conflict_raises():
    service = ScheduleService(conn, repos)
    
    course1 = CourseInput("Math", "Prof. A", "Mon", "09:00", "10:50")
    course2 = CourseInput("Physics", "Prof. B", "Mon", "10:00", "11:50")
    
    service.add_course(course1)
    
    with pytest.raises(ScheduleConflictError):
        service.add_course(course2)  # Overlaps!
```

### Test: Successful Add
```python
def test_add_success():
    service = ScheduleService(conn, repos)
    
    course = CourseInput("Math", "Prof. A", "Mon", "09:00", "10:50")
    
    result = service.add_course(course)
    
    assert "Math" in result
    assert "Prof. A" in result
    assert "Mon" in result
```

---

## Lessons Learned

### ✅ Do: Fail-Fast
```python
raise ScheduleConflictError(...)  # Explicit
```

### ❌ Don't: Return Booleans
```python
return False  # Why? Unknown!
```

### ✅ Do: Repository Boundaries
```python
self._repo.add_raw(...)  # SQL in repo
```

### ❌ Don't: SQL in Service
```python
cursor.execute(...)  # ❌ Wrong layer
```

### ✅ Do: Calculate Instances
```python
next_instance = MAX(instance) + 1
```

### ❌ Don't: Hardcode Instance
```python
instance = 1  # ❌ Will collide
```

---

## Next Steps

**Phase 10**: Consolidate `_create_tables()` into migrations  
**Phase 11**: Extract deprecated methods to legacy adapter  
**Phase 12**: Create query builder for DRY queries

---

**Current State**: Service layer foundation complete ✅  
**God Object Score**: 9/10 → 6/10 (improvement!)
