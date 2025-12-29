# Phase 6 Walkthrough: Formatter Separation

**Date**: 30.12.2024  
**Commits**: `[hash1]`, `[hash2]`  
**Status**: ✅ Complete

---

## Objective
Separate UI string formatting logic from the model layer, implementing the principle: **Model = Data, Formatter = Display**.

---

## Problem Statement

**Before**: Formatting logic scattered in model
```python
# In ScheduleModel.add_course
saat = f"{baslangic}-{bitis}"
course_info = f"[{current_code}] {ders_adi} - {hoca_adi} ({gun} {saat}){classes_str}"
self.course_added.emit(course_info)
```

**Issues**:
- ❌ Model knows about UI format
- ❌ Formatting logic not reusable
- ❌ Hard to change display format
- ❌ Testing requires parsing strings

---

## Solution: ScheduleFormatter

### Created Files

**Location**: `models/formatters/schedule_formatter.py` (129 lines)

**Structure**:
```python
class ScheduleFormatter:
    # Primitive formatters
    format_time_range(start, end) -> str
    format_day_time(day, start, end) -> str
    format_course(code, name, teacher, ...) -> str
    
    # Entity-aware formatter
    from_scheduled_course(course) -> str
```

---

## Evolution: Three Iterations

### Iteration 1: Basic Formatter
```python
@staticmethod
def format_course(code, name, teacher, day, start, end, ...):
    time_range = f"{start}-{end}"  # Inline
    parts = [f"[{code}] {name}"]
    parts.append(f"- {teacher} ({day} {time_range})")  # Inline
    return " ".join(parts)
```

**Problem**: Time formatting repeated

### Iteration 2: Added Helpers
```python
@staticmethod
def format_time_range(start, end):
    return f"{start}-{end}"

@staticmethod
def format_day_time(day, start, end):
    return f"{day} {format_time_range(start, end)}"  # ❌ Not using self
```

**Problem**: Helpers exist but not used by main method

### Iteration 3: DRY (Final) ✅
```python
@staticmethod
def format_time_range(start, end):
    return f"{start}-{end}"

@staticmethod
def format_day_time(day, start, end):
    return f"{day} {ScheduleFormatter.format_time_range(start, end)}"

@staticmethod
def format_course(code, name, teacher, day, start, end, ...):
    parts = [f"[{code}] {name}"]
    if pools:
        parts.append(f"[{pools}]")
    
    # DRY: Uses helper
    parts.append(
        f"- {teacher} ({ScheduleFormatter.format_day_time(day, start, end)})"
    )
    
    if classes:
        parts.append(f"[{classes}]")
    
    return " ".join(parts)
```

**Benefits**:
- ✅ Single source of truth for time formatting
- ✅ Easy to change format globally
- ✅ Composable methods

---

## Entity-Aware Formatting

### Added Convenience Method

```python
@staticmethod
def from_scheduled_course(course: "ScheduledCourse") -> str:
    """
    Format a ScheduledCourse entity for display.
    Repository stays UI-agnostic. Formatter bridges entity → display.
    """
    return ScheduleFormatter.format_course(
        code=course.ders_kodu,
        name=course.ders_adi,
        teacher=course.hoca,
        day=course.gun,
        start=course.baslangic,
        end=course.bitis,
        classes=course.siniflar,
        pools=course.havuz_kodlari
    )
```

**Usage Comparison**:

**Primitive Style**:
```python
# Manual field extraction
course = repo.get_by_id(123)
display = formatter.format_course(
    code=course.ders_kodu,
    name=course.ders_adi,
    teacher=course.hoca,
    # ... 6 more fields
)
```

**Entity Style** ✅:
```python
# Clean and simple
course = repo.get_by_id(123)
display = formatter.from_scheduled_course(course)
```

**Key Principle**: Repository returns entities, formatter knows how to display them, **but repository doesn't know about formatting**.

---

## Layer Boundaries

```
┌─────────────────────────────────────┐
│         View Layer (UI)             │
│  - Calls formatter methods          │
│  - Displays formatted strings       │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│      Formatter Layer                │
│  - format_course()                  │
│  - from_scheduled_course()          │
│  - Knows display format             │
│  - NO business logic                │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│       Model Layer                   │
│  - Returns entities/data            │
│  - NO string formatting             │
│  - Calls formatter when needed      │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│    Repository Layer                 │
│  - Returns ScheduledCourse entities │
│  - NO UI knowledge                  │
└─────────────────────────────────────┘
```

**Separation Achieved**: Each layer has clear responsibilities, no bleeding of concerns.

---

## Integration with schedule_model.py

### Refactored add_course

**Before (18 lines with formatting)**:
```python
# Fetch connected classes for display
self.c.execute('''
    SELECT GROUP_CONCAT(DISTINCT b.bolum_adi || ' ' || od.sinif_duzeyi || '. Sınıf')
    FROM Ders_Sinif_Iliskisi dsi
    JOIN Ogrenci_Donemleri od ON dsi.donem_sinif_num = od.donem_sinif_num
    JOIN Bolumler b ON od.bolum_num = b.bolum_id
    WHERE dsi.ders_instance = ? AND dsi.ders_adi = ?
''', (instance, ders_adi))
class_row = self.c.fetchone()
classes_str = f" [{class_row[0]}]" if class_row and class_row[0] else ""

# Emit signal
saat = f"{baslangic}-{bitis}"
# Format: [Code] Name - Teacher (Day Time) [Classes]
course_info = f"[{current_code}] {ders_adi} - {hoca_adi} ({gun} {saat}){classes_str}"
self.course_added.emit(course_info)
return True
```

**After (8 lines with formatter)**:
```python
# Emit signal with formatted course info
from models.formatters import ScheduleFormatter

course_info = ScheduleFormatter.format_course(
    code=current_code,
    name=ders_adi,
    teacher=hoca_adi,
    day=gun,
    start=baslangic,
    end=bitis,
    classes=classes_str.strip('[] ') if classes_str else None
)
self.course_added.emit(course_info)
return True
```

**Reduction**: 18 lines → 8 lines (56% reduction in formatting section)

---

## Public API Clarity

### Added `__all__`

```python
__all__ = ["ScheduleFormatter"]
```

**Benefits**:
- ✅ Clear public interface
- ✅ IDE autocomplete knows what's public
- ✅ `from models.formatters import *` is safe (though not recommended)
- ✅ Documentation clarity

---

## Code Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Formatting in model** | Inline | Isolated | ✅ |
| **Reusable formatters** | 0 | 4 methods | ✅ |
| **DRY compliance** | No | Yes | ✅ |
| **Entity-aware** | No | Yes | ✅ |
| **Test coverage** | Hard | Easy | ✅ |

---

## Benefits

### 1. Easy to Change Format

**Change time format globally**:
```python
# Before: change in 5+ places
saat = f"{baslangic}-{bitis}"

# After: change in ONE place
@staticmethod
def format_time_range(start, end):
    return f"{start}—{end}"  # Changed - to — (em dash)
    # All displays update automatically ✅
```

### 2. Testable Without DB

```python
def test_format_course():
    result = ScheduleFormatter.format_course(
        code="MAT101",
        name="Matematik",
        teacher="Prof. Dr. Ali",
        day="Pazartesi",
        start="09:00",
        end="10:50"
    )
    
    assert result == "[MAT101] Matematik - Prof. Dr. Ali (Pazartesi 09:00-10:50)"
    # No database, no models, pure logic test ✅
```

### 3. Layer Independence

```python
# Repository doesn't know about formatting
repo = ScheduleRepository(cursor, conn)
course = repo.get_by_id(123)  # Returns ScheduledCourse entity

# Formatter doesn't know about database
formatter = ScheduleFormatter()
display = formatter.from_scheduled_course(course)  # Pure function

# ✅ Each layer testable in isolation
```

### 4. UI Flexibility

```python
# Same data, different formats
course = repo.get_by_id(123)

# For list display
list_format = ScheduleFormatter.from_scheduled_course(course)

# For calendar tooltip (future)
tooltip = ScheduleFormatter.format_tooltip(course)  # Easy to add

# For export (future)
csv_row = ScheduleFormatter.to_csv(course)  # Easy to add
```

---

## Design Patterns Applied

### 1. Separation of Concerns
- Model: business logic & data
- Formatter: presentation logic
- View: user interaction

### 2. Single Responsibility
- Formatter only formats
- Doesn't query DB
- Doesn't validate
- Doesn't transform data

### 3. Open/Closed Principle
```python
# Can add new formatters without changing existing ones
class ScheduleFormatter:
    # Existing methods unchanged
    
    # New formats added easily
    @staticmethod
    def format_calendar_tooltip(course): ...
    
    @staticmethod
    def format_excel_export(course): ...
```

---

## Files Modified

- `models/formatters/__init__.py` - New (+7 lines)
- `models/formatters/schedule_formatter.py` - New (+129 lines)
- `models/schedule_model.py` - Integration
  - `add_course`: Use formatter (-10 lines inline formatting)

**Net Impact**: +136 lines (new formatter), -10 lines (inline formatting)

---

## Future Extensions (Easy Now)

With formatter in place, these become trivial:

```python
# 1. Multiple languages
@staticmethod
def format_course_en(code, name, ...):
    return f"[{code}] {name} - {teacher} ({day} {time})"

@staticmethod  
def format_course_tr(code, name, ...):
    return f"[{code}] {name} - {teacher} ({gun} {saat})"

# 2. Different display contexts
@staticmethod
def format_for_pdf(course): ...

@staticmethod
def format_for_email(course): ...

# 3. Accessibility
@staticmethod
def format_for_screen_reader(course): ...
```

---

## Lessons Learned

### Do: Compose Methods
```python
✅ format_course() uses format_day_time()
✅ format_day_time() uses format_time_range()
```

### Don't: Repeat Logic
```python
❌ time_range = f"{start}-{end}"  # Repeated everywhere
✅ ScheduleFormatter.format_time_range(start, end)  # One place
```

### Do: Entity-Aware Helpers
```python
✅ from_scheduled_course(course)  # Convenience for common case
```

### Don't: Mix Concerns
```python
❌ Formatter queries database
❌ Repository formats strings
✅ Clear separation ✅
```

---

## Next Phase
Phase 7: Add transaction boundaries and error handling with `with self.conn:` blocks.
