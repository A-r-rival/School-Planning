
import sys
import unittest
from unittest.mock import patch, MagicMock

# Mock the imports used in populate_students
sys.modules['models'] = MagicMock()
sys.modules['models.schedule_model'] = MagicMock()
sys.modules['scripts.curriculum_data'] = MagicMock()

# Define mock data
MOCK_DEPT_DATA = {
    "Engineering": {
        "TestDept": {
            "pools": {
                "SDUa": [("C1", "Course 1", 6)],
                "SDUb": [("C2", "Course 2", 6)],
                "SDUc": [("C3", "Course 3", 6)],
                "OtherPool": [("C4", "Course 4", 6)],
                "SDUHeader": [] # Should be ignored (too long)
            }
        }
    }
}

# Now verify the logic by importing/copying the function
# Easier to just create a small script that monkeypatches DEPARTMENTS_DATA and calls the function
import sys
import os

# Create a temporary test file that imports the modified script
with open('test_sdux_run.py', 'w', encoding='utf-8') as f:
    f.write('''
import sys
import os
sys.path.append(os.getcwd())

# Mock data BEFORE importing populate_students
import scripts.populate_students as ps
from scripts.populate_students import get_courses_for_slot

# Setup mock data
ps.DEPARTMENTS_DATA = {
    "Fac": {
        "Dept": {
            "pools": {
                "SDUa": [("C1", "Course 1", 6)],
                "SDUb": [("C2", "Course 2", 6)],
                "SDP": [("P1", "Project", 6)]
            }
        }
    }
}

print("Testing SDUx wildcard logic...")
courses = get_courses_for_slot("SDUx", "Dept", "Fac", 6)

if courses:
    print(f"Found {len(courses)} courses.")
    names = sorted([c[1] for c in courses])
    print(f"Courses: {names}")
    
    if "Course 1" in names and "Course 2" in names:
        print("SUCCESS: Retrieved courses from both SDUa and SDUb")
    else:
        print("FAILURE: Did not retrieve expected courses")
else:
    print("FAILURE: No courses found for SDUx")

print("\\nTesting normal pool logic (SDP)...")
courses_p = get_courses_for_slot("SDP", "Dept", "Fac", 6)
if courses_p and courses_p[0][0] == "P1":
    print("SUCCESS: Normal pool logic works")
else:
    print("FAILURE: Normal pool logic broken")

''')
