# Phase 2: Calendar Builder Service

**Date**: 30.12.2024  
**Status**: ✅ Complete  
**Impact**: Controller 670 → 496 lines (-174 lines, -26%)

---

## Problem

`handle_calendar_filter()` was 258 lines doing:
- Data fetching (teacher/classroom/student views)
- Elective detection (curriculum + regex)
- Multiple tuple formats (6/7/8/9 items)
- Formatting and post-processing
- Merging logic

---

## Solution

**Created**: `services/calendar_schedule_builder.py` (455 lines)

### Key Innovation: Single Tuple Format

```python
# ALL internal data uses 9-tuple:
(day, start, end, display, extra,
 is_elective, real_name, code, pools)
```

**Benefits**:
- No more `len(item)` branching
- Builders pad missing fields
- Strip helpers (not magic `[:5]`)
- Future dataclass migration = trivial

---

## Controller Transformation

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
            for item in raw:
                if len(item) == 7:
                    # ... tuple unpacking
                elif len(item) == 6:
                    # ... different handling
        elif "classroom_id" in data:
            # ... 50+ more lines
        elif "faculty_id" in data:
            # ... 150+ lines with elective detection
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
            items = self.calendar_builder.get_departments_for_faculty(data["faculty_id"])
            self.calendar_view.update_filter_options(2, items)
            return
        
        # Build and display
        schedule_data = self.calendar_builder.build(data)
        self.calendar_view.display_schedule(schedule_data)
        if schedule_data:
            self.calendar_view.show()
```

---

## User Feedback Applied

✅ **Single canonical tuple** - all builders normalize to 9-tuple  
✅ **Strip helpers** - intent-revealing, not magic slicing  
✅ **Safer conditions** - `data.get()` instead of `'key' in data`  
✅ **TODO breadcrumbs** - ElectiveDetector, StudentScheduleGrouper extraction marked  

---

## Metrics

| Metric | Before | After | Reduction |
|--------|--------|-------|-----------|
| Controller | 670 | 496 | **-174 (-26%)** |
| Calendar method | 258 | 23 | **-235 (-91%)** |
| Tuple formats | 5+ | 1 | **-80%** |

**Cumulative**: 854 → 496 lines (**-42%**)

---

**Status**: Complete ✅  
**Walkthrough**: [Phase_2_Calendar_Builder.md](./Phase_2_Calendar_Builder.md)
