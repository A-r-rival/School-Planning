# Controller Refactoring Walkthrough

**Goal**: Transform ScheduleController from 854-line God Object into clean MVC coordinator

**Strategy**: Surgical refactoring - safe, independent slices

---

## Overview

ScheduleController was doing **6 jobs**:
1. ✅ MVC orchestration (CORRECT)
2. ❌ View formatting
3. ❌ Business rules
4. ❌ Curriculum/elective detection
5. ❌ Data reshaping algorithms
6. ❌ Legacy compatibility

**Target**: Controller should only do #1

---

## Metrics Progress

| Phase | Lines | Change | Status |
|-------|-------|--------|--------|
| **Start** | 854 | - | - |
| **Phase 1** | 670 | -134 (-16%) | ✅ Complete |
| **Phase 2** | ~270 | ~-400 | 🔄 In Progress |
| **Phase 3** | ~220 | ~-50 | Planned |
| **Phase 4** | ~200 | ~-20 | Planned |

---

## Completed Phases

### ✅ Phase 1: Pure Utilities (Complete)

**Extracted**: `utils/schedule_merger.py` (180 lines)

**Functions**:
- `merge_course_strings()` - Merges consecutive course blocks in string format
- `merge_consecutive_blocks()` - Merges consecutive course blocks in tuple format

**Benefits**:
- Pure functions (zero dependencies)
- Easy to test
- No Qt, no Model
- Zero behavior change

**Impact**: 854 → 670 lines (-134, -16%)

**Walkthrough**: See [Phase_1_Utilities.md](./Phase_1_Utilities.md)

---

## In Progress

### 🔄 Phase 2: Calendar Builder Service

**Extract**: Calendar schedule construction logic from `handle_calendar_filter()`

**Problem**: 400+ lines mixing:
- Data fetching from model
- Type checking logic
- Elective detection
- Formatting logic
- Merging algorithms

**Create**: `services/calendar_schedule_builder.py`

**Target**:
```python
# Before: 400 lines
def handle_calendar_filter(self, event_type, data):
    # Massive complex logic...
    
# After: 3 lines
def handle_calendar_filter(self, event_type, data):
    schedule = self.calendar_builder.build(event_type, data)
    self.calendar_view.display_schedule(schedule)
```

**Estimated Impact**: 670 → ~270 lines (-400, -60%)

---

## Planned Phases

### Phase 3: Elective Domain Logic

**Extract**: Curriculum and pool detection logic

**Create**: `domain/elective_resolver.py`

**Impact**: ~50 lines of domain knowledge isolated

### Phase 4: UI Presentation

**Clean**: QMessageBox confirmations, dialog logic

**Impact**: ~20 lines, cleaner separation

---

## Final Target: "Boring Controller"

Controller should be **glue code only**:
- Wire signals ✅
- Call services ✅
- Forward results to views ✅
- Ask questions (don't decide) ✅
- Never parse strings ✅
- Never inspect tuples by index ✅
- No business logic ✅

---

**Last Updated**: Phase 1 Complete (30.12.2024)
