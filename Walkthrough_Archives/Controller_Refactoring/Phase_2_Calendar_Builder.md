# Phase 2: Calendar Builder Service Extraction

**Date**: 30.12.2024  
**Status**: ✅ Complete (with refinements)  
**Impact**: 670 → 496 lines (-174 lines, -26%)

---

## Problem

ScheduleController had a massive 258-line `handle_calendar_filter()` method doing:
- Data fetching from model
- Type checking (teacher/classroom/student views)
- Elective detection with curriculum lookup
- Formatting tuples
- Merging consecutive blocks
- Post-processing for student views

**Issues**:
- Business logic in controller
- Tuple-shape explosion (5+ different formats)
- Hard to test
- Hard to reuse

---

## Solution

Extract to dedicated service: `services/calendar_schedule_builder.py`

### Created Files

```
services/
├── __init__.py
└── calendar_schedule_builder.py  # 455 lines
```

---

## Extraction Details

### CalendarScheduleBuilder Methods

**Public API**:
- `build_for_type_change(view_type)` - Get filter options
- `build(data)` - Main builder method
- `get_departments_for_faculty(faculty_id)` - Department dropdown

**Internal Builders**:
- `_build_teacher_schedule()` - Teacher view data
- `_build_classroom_schedule()` - Classroom view data
- `_build_student_group_schedule()` - Student view data
- `_process_student_schedule()` - With elective detection

**Domain Logic**:
- `_detect_elective()` - Curriculum + regex detection

**Formatting**:
- `_strip_for_regular_view()` - Teacher/classroom display
- `_strip_for_core_student()` - Student core courses
- `_post_process_student_view()` - Group electives

---

## Key Improvement: Tuple Normalization

### Problem Identified
Original code had tuple-shape explosion:
```python
# Different tuple lengths everywhere
if len(item) == 6:
elif len(item) == 7:
elif len(item) == 8:
# Then magic slicing: item[:5], item[:7], item[:9]
```

### Solution Applied

**Single Canonical Format** (documented in docstring):
```python
# ALL internal data uses 9-tuple:
(day, start, end, display_course, extra_info,
 is_elective, real_course_name, course_code, pool_codes)
```

**All builders normalize**:
```python
# Teacher/Classroom (no electives): pad with defaults
schedule_data.append((
    day, start, end, display, extra,
    False,  # is_elective
    course, # real_name
    code,   # course_code
    []      # pool_codes (empty)
))

# Student (with detection): full tuple
schedule_data.append((
    day, start, end, display, extra,
    is_elective, course, code, pool_codes
))
```

**Strip helpers** (not magic slicing):
```python
def _strip_for_regular_view(self, item):
    return item[:5]  # Intent clear, easy to change

# When migrating to dataclass:
def _strip_for_regular_view(self, item: ScheduleItem):
    return (item.day, item.start, item.end, 
            item.display, item.extra)
```

---

## Controller Changes

### Before (258 lines)
```python
def handle_calendar_filter(self, event_type, data):
    if event_type == "type_changed":
        if view_type == "Öğretmen":
            items = self.model.get_all_teachers_with_ids()
            self.calendar_view.update_filter_options(1, items)
        elif view_type == "Derslik":
            # ... 50 more lines
        
    elif event_type == "filter_selected":
        schedule_data = []
        if "teacher_id" in data:
            raw = self.model.get_schedule_by_teacher(...)
            for item in raw:
                if len(item) == 7:
                    # ... 10 lines
                elif len(item) == 6:
                    # ... 10 lines
        elif "classroom_id" in data:
            # ... 50 more lines
        elif "faculty_id" in data:
            # ... 150 more lines (!!!)
            # Massive elective detection
            # Curriculum lookups
            # Pool code extraction
            # Regex matching
```

### After (23 lines)
```python
def handle_calendar_filter(self, event_type, data):
    if event_type == "type_changed":
        result = self.calendar_builder.build_for_type_change(data["type"])
        if result:
            filter_level, items = result
            self.calendar_view.update_filter_options(filter_level, items)
    
    elif event_type == "filter_selected":
        # Check for department dropdown update
        if data.get("faculty_id") and not data.get("dept_id"):
            items = self.calendar_builder.get_departments_for_faculty(
                data["faculty_id"]
            )
            self.calendar_view.update_filter_options(2, items)
            return
        
        # Build and display
        schedule_data = self.calendar_builder.build(data)
        self.calendar_view.display_schedule(schedule_data)
        if schedule_data:
            self.calendar_view.show()
```

**Result**: Pure MVC glue code ✅

---

## Benefits

### ✅ Separation of Concerns
- Business logic (elective detection) in service
- Controller = pure orchestration
- No curriculum imports in controller

### ✅ Single Responsibility
- Service knows HOW to build schedules
- Controller knows WHEN to build schedules

### ✅ Testability
- Can test builder without Qt
- Can test builder without views
- Can mock model easily

### ✅ Reusability
- Other controllers can use builder
- Calendar export can use builder
- API endpoints can use builder

### ✅ Maintainability
- Tuple normalization = future-proof
- Only strip helpers change for dataclass migration
- Clear intent everywhere

---

## Engineering Lessons Applied

### User Feedback Integration

**Identified Issues**:
1. Tuple-shape explosion
2. Magic number slicing
3. Unsafe dictionary access
4. No future migration path

**Applied Fixes**:
1. ✅ Single canonical 9-tuple format
2. ✅ Intent-revealing strip helpers
3. ✅ `data.get()` instead of `'key' in data`
4. ✅ Clear migration path documented

### TODO Breadcrumbs
```python
# TODO (post-model-refactor):
# - Extract ElectiveDetector as separate service
# - Extract StudentScheduleGrouper as separate service
```

Not splitting now = avoids multiplying moving parts during refactor.

---

## Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **Controller Lines** | 670 | 496 | **-174 (-26%)** |
| **Service Lines** | 0 | 455 | +455 |
| **handle_calendar_filter** | 258 lines | 23 lines | **-235 (-91%)** |
| **Tuple Formats** | 5+ | 1 | **-80%** |
| **Curriculum Imports** | Controller | Service | ✅ Moved |

---

## Cumulative Progress

| Phase | Lines Removed | Controller Size |
|-------|---------------|-----------------|
| **Start** | - | 854 |
| **Phase 1** | -134 | 670 |
| **Phase 2** | -174 | **496** |
| **Total** | **-358 (-42%)** | **496** |

---

## Next Steps

**Phase 3**: Domain logic extraction (optional)
- Could extract `ElectiveDetector`
- Would further slim service
- Wait until model refactor complete

**Status**: Phase 2 complete and refined ✅

---

**Generated**: 30.12.2024  
**Phase 2**: Complete with tuple normalization ✅
