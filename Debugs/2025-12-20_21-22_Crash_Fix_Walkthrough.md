# Debugging 'ders programı yap' Crash

I have fixed the application crash that occurred when clicking "ders programı yap".

## The Issue
The crash was caused by two separate issues:
1. **Uninitialized Scheduler**: The `ORToolsScheduler` class attempted to solve the model without loading data or creating variables first.
2. **Library Conflict**: Importing `PyQt5` before `ORTools` caused a hard crash (segmentation fault) due to conflicting `protobuf` library versions.

## The Fix

### 1. Scheduler Initialization
Updated `controllers/scheduler.py` to ensure `load_data()`, `create_variables()`, and `add_hard_constraints()` are called before solving.

```python
    def solve(self):
        """Solve the scheduling problem"""
        # Initialize model
        self.load_data()
        self.create_variables()
        self.add_hard_constraints()
        
        # ... solving logic ...
```

### 2. Import Order
Updated `main.py` to import `ortools` *before* `PyQt5`. This ensures the correct underlying libraries are loaded first.

```python
import sys
import os

# Import ORTools first to avoid conflict with PyQt5 (protobuf versions)
try:
    from ortools.sat.python import cp_model
except ImportError:
    pass

from PyQt5.QtWidgets import QApplication
# ...
```

## Verification
- Created a reproduction script `repro_crash.py` that mimicked the crash.
- Confirmed the crash was resolved after applying both fixes.
- Verified that ORTools acts correctly on the user's data (finding an OPTIMAL solution for the test set).
