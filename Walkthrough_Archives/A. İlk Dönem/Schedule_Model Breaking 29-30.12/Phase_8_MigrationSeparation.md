# Phase 8 Walkthrough: Migration Separation

**Date**: 30.12.2024  
**Status**: ✅ Complete

---

## Objective
Extract database migration logic from `ScheduleModel` into a dedicated migration module.

---

## Problem Statement

**Before**: Migration code mixed with business logic
```python
class ScheduleModel:
    def __init__(self):
        self._create_tables()  # 200 lines of CREATE TABLE
        self._check_and_migrate_teacher_table()  # 27 lines
```

**Issues**:
- ❌ Model responsible for schema
- ❌ Migration logic scattered
- ❌ No migration history
- ❌ Hard to add new migrations

---

## Solution: DatabaseMigration Module

### Created: `models/repositories/migration.py`

```python
class DatabaseMigration:
    """
    Manages database schema migrations.
    - Idempotent
    - Transaction-safe
    - Ordered
    """
    
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn
    
    def run_all(self) -> None:
        for migration in self._migrations():
            migration()
    
    def _migrations(self) -> Iterable[Callable]:
        return [
            self._add_preferred_day_span_to_teachers,
            # Add future migrations here
        ]
```

---

## Registry Pattern

### Migration List
```python
def _migrations(self):
    """
    Ordered list of migration steps.
    Add new migrations here.
    """
    return [
        self._001_add_preferred_day_span,
        # self._002_add_course_prerequisites,  # Future
        # self._003_add_room_capacity,         # Future
    ]
```

**Benefits**:
- ✅ Clear execution order
- ✅ Easy to add new migrations
- ✅ Self-documenting history

---

## Helper Methods

### 1. Column Existence Check
```python
def _column_exists(self, table: str, column: str) -> bool:
    cursor = self._conn.execute(f"PRAGMA table_info({table})")
    return column in {row[1] for row in cursor.fetchall()}
```

**Usage**:
```python
if self._column_exists("Ogretmenler", "preferred_day_span"):
    return  # Skip migration
```

### 2. Logging
```python
def _log(self, message: str) -> None:
    print(f"[MIGRATION] {message}")
```

**Output**:
```
[MIGRATION] Adding preferred_day_span column to Ogretmenler
[MIGRATION] ✅ Ogretmenler migrated successfully
```

---

## Migration Example

```python
def _add_preferred_day_span_to_teachers(self) -> None:
    """
    Adds preferred_day_span column to Ogretmenler table.
    """
    # Idempotent check
    if self._column_exists("Ogretmenler", "preferred_day_span"):
        return
    
    self._log("Adding preferred_day_span column to Ogretmenler")
    
    # Transaction-safe
    with self._conn:
        self._conn.execute(
            """
            ALTER TABLE Ogretmenler
            ADD COLUMN preferred_day_span INTEGER DEFAULT NULL
            """
        )
    
    self._log("✅ Ogretmenler migrated successfully")
```

---

## Integration with ScheduleModel

### Before
```python
class ScheduleModel:
    def __init__(self):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        self._check_and_migrate_teacher_table()  # Inline migration
        
    def _check_and_migrate_teacher_table(self):
        # 27 lines of migration code
        ...
```

### After
```python
class ScheduleModel:
    def __init__(self):
        self.conn = sqlite3.connect(db_path)
        self.c = self.conn.cursor()
        self.c.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        
        # Run database migrations
        from models.repositories.migration import DatabaseMigration
        migration = DatabaseMigration(self.conn)
        migration.run_all()
```

**Reduction**: 27 lines removed from ScheduleModel ✅

---

## Design Decisions

### 1. Only `conn` Parameter
```python
def __init__(self, conn: sqlite3.Connection):
    self._conn = conn
```

**Why not cursor?**
- Migration creates own cursors as needed
- Cleaner API
- Matches transaction pattern

### 2. Transaction Per Migration
```python
with self._conn:
    self._conn.execute("ALTER TABLE ...")
```

**Benefits**:
- Each migration atomic
- Failure isolates to one migration
- Easy to retry

### 3. Idempotent Checks
```python
if self._column_exists(...):
    return  # Safe to run multiple times
```

**Why important?**
- App restart doesn't re-migrate
- Development cycles safe
- Production deploys safe

---

## Code Metrics

| Metric | Before | After |
|--------|--------|-------|
| **Migration in model** | 27 lines | 0 lines |
| **Migration module** | 0 | 70 lines |
| **Separation** | No | Yes ✅ |
| **Reusability** | No | Yes ✅ |
| **Testability** | Hard | Easy ✅ |

---

## Future Extensions

### Adding New Migration
```python
def _migrations(self):
    return [
        self._001_add_preferred_day_span,
        self._002_add_room_capacity,  # NEW
    ]

def _002_add_room_capacity(self):
    if self._column_exists("Derslikler", "capacity"):
        return
    
    self._log("Adding capacity to Derslikler")
    
    with self._conn:
        self._conn.execute(
            "ALTER TABLE Derslikler ADD COLUMN capacity INTEGER"
        )
    
    self._log("✅ Derslikler migrated")
```

**Just add to list!** No touching existing code ✅

---

## Comparison with Other Patterns

### Django-style Migrations
```python
# migration_0001.py
def forward(apps, schema_editor):
    schema_editor.add_column(...)
```

**Our approach is simpler** because:
- No schema abstraction needed
- Direct SQL okay for small project
- Easier to understand

### Alembic-style
```python
def upgrade():
    op.add_column(...)

def downgrade():
    op.drop_column(...)
```

**We skip downgrade** because:
- Small project
- Manual rollback acceptable
- Simpler code

---

## Testing Strategy

### Test: Idempotent
```python
def test_migration_idempotent():
    migration = DatabaseMigration(conn)
   migration.run_all()
    migration.run_all()  # Run again
    # Should not error ✅
```

### Test: Column Added
```python
def test_adds_column():
    migration = DatabaseMigration(conn)
    migration.run_all()
    
    cursor = conn.execute("PRAGMA table_info(Ogretmenler)")
    columns = [row[1] for row in cursor.fetchall()]
    
    assert 'preferred_day_span' in columns
```

---

## Lessons Learned

### ✅ Do: Keep Migrations Small
```python
def _add_one_column(self):
    # Small, focused migration
```

### ❌ Don't: Combine Multiple Changes
```python
def _big_migration(self):
    # Add 5 columns
    # Rename 3 tables
    # Change data types
    # ❌ Too much, hard to debug
```

### ✅ Do: Log Everything
```python
self._log("Starting migration X")
# ... migration code
self._log("✅ Migration X complete")
```

### ✅ Do: Use Transactions
```python
with self._conn:
    # Schema change
```

---

## Next Phase
Phase 9: Extract business logic into ScheduleService for better testability and separation of concerns.
