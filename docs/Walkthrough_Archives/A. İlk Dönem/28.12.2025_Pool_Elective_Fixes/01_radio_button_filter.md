# Radio Button Filter Implementation

## Problem Statement
User requested filter options for course list view to show:
- All courses
- Only elective courses
- Only mandatory/core courses

Initial implementation used two checkboxes which created ambiguity:
- What if both checked?
- What if neither checked?
- Confusing "Sadece Zorunlu Dersler" with "Zorunlu Seçmeli" pool courses

## Solution: Radio Buttons

### Design Decision
Replaced two independent checkboxes with three mutually exclusive radio buttons:
- ◉ Tüm Dersler (default)
- ○ Sadece Doğrudan Zorunlu
- ○ Sadece Seçmeli

**Advantages:**
- Clear mutual exclusivity
- Explicit default state
- Better UX - one click to change filter
- Avoided naming confusion with "Zorunlu Seçmeli" pools

### Implementation

#### 1. UI Changes (`views/schedule_view.py`)

**Before:**
```python
self.filter_only_elective = QCheckBox("Sadece Seçmeli Dersler")
self.filter_only_core = QCheckBox("Sadece Zorunlu Dersler")
```

**After:**
```python
from PyQt5.QtWidgets import QRadioButton, QButtonGroup

self.course_type_group = QButtonGroup()

self.filter_all_courses = QRadioButton("Tüm Dersler")
self.filter_all_courses.setChecked(True)  # Default

self.filter_only_core = QRadioButton("Sadece Doğrudan Zorunlu")
self.filter_only_elective = QRadioButton("Sadece Seçmeli")

# Add to button group for mutual exclusivity
self.course_type_group.addButton(self.filter_all_courses)
self.course_type_group.addButton(self.filter_only_core)
self.course_type_group.addButton(self.filter_only_elective)
```

**Key Points:**
- `QButtonGroup` ensures only one radio button selected
- Default to "Tüm Dersler" for familiar UX
- Renamed "Zorunlu Dersler" → "Sadece Doğrudan Zorunlu" to avoid confusion

#### 2. Filter Logic (`controllers/schedule_controller.py`)

```python
# 4. Apply Elective/Core Filters
only_elective = filters.get("only_elective", False)
only_core = filters.get("only_core", False)

# If both checked or neither checked, show all
if only_elective and not only_core:
    # Show only electives - check for "Seçmeli" in course string
    courses = [c for c in courses if "seçmeli" in c.lower()]
elif only_core and not only_elective:
    # Show only cores (not seçmeli)
    courses = [c for c in courses if "seçmeli" not in c.lower()]
# else: show all (both checked or neither checked)
```

**Logic:**
- Mutually exclusive by design
- Filters based on "seçmeli" keyword in course name
- Default: show all if neither explicitly selected (shouldn't happen with radio buttons)

## Testing

### Test Cases
1. ✅ Default state shows all courses
2. ✅ Selecting "Sadece Seçmeli" filters to electives only
3. ✅ Selecting "Sadece Doğrudan Zorunlu" filters to core only
4. ✅ Switching between options updates list correctly
5. ✅ Only one option selectable at a time

### User Feedback
- Initially filter showed empty → root cause was missing pool data (separate issue)
- After pool data populated, filtering works correctly

## Files Modified
- [schedule_view.py:264-291](file:///d:/Git_Projects/School-Planning/views/schedule_view.py#L264-L291) - Radio button UI
- [schedule_view.py:334-360](file:///d:/Git_Projects/School-Planning/views/schedule_view.py#L334-L360) - Filter state extraction
- [schedule_controller.py:348-363](file:///d:/Git_Projects/School-Planning/controllers/schedule_controller.py#L348-L363) - Filter logic

## Lessons Learned
- Radio buttons better than checkboxes for mutually exclusive options
- Clear naming prevents confusion (especially with similar terms like "Zorunlu" and "Zorunlu Seçmeli")
- Default state should be obvious and familiar to users

## Related Issues
- Empty filter results → Led to pool data foundation work (see [04_parse_curriculum_pools.md](04_parse_curriculum_pools.md))
