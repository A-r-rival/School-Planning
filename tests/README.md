# Tests Package

Unit tests for School Planning application.

## Running Tests

```bash
# Install pytest
pip install pytest

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_schedule_service.py

# Run specific test
pytest tests/test_schedule_service.py::TestScheduleServiceAddCourse::test_teacher_conflict_raises_error
```

## Test Structure

- `conftest.py` - Pytest fixtures (in-memory database, repositories, service)
- `test_schedule_service.py` - ScheduleService business logic tests

## Benefits

✅ No real database needed - in-memory SQLite
✅ Fast execution (milliseconds)
✅ Clean isolation - each test gets fresh database
✅ Easy to write - fixtures handle setup
✅ No Qt dependency - pure Python

## Example Test

```python
def test_teacher_conflict_raises_error(schedule_service):
    # Add first course
    course1 = CourseInput(...)
    schedule_service.add_course(course1)
    
    # Try to add conflicting course
    course2 = CourseInput(...)  # Same teacher, same time
    
    with pytest.raises(ScheduleConflictError):
        schedule_service.add_course(course2)
```
